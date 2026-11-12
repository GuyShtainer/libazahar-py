// Minimal headless libretro frontend: offscreen CGL GL core context, no window. Usage:
// fe core.dylib content sysdir outdir seconds shot_frames(comma) ; core options via env OPT_<key>=value
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdbool.h>
#include <dlfcn.h>
#include <time.h>
#include <zlib.h>
#include <OpenGL/OpenGL.h>
#include <OpenGL/gl3.h>
#define VK_ENABLE_BETA_EXTENSIONS
#include <vulkan/vulkan.h>
#include <libretro_vulkan.h>
#include <pthread.h>

struct geom{unsigned bw,bh,mw,mh;float ar;};
struct avinfo{struct geom g;double fps,sr;};
struct gameinfo{const char*path;const void*data;size_t size;const char*meta;};
struct var{const char*key;const char*value;};
struct hwr{unsigned type;void(*reset)(void);uintptr_t(*getfb)(void);void*(*getproc)(const char*);bool depth,stencil,bl;unsigned vmaj,vmin;bool cache;void(*destroy)(void);bool debug;};

static const char*sysdir,*outdir;
static struct hwr hw; static bool have_hw; static CGLContextObj ctx; static GLuint fbo,tex,rb; static unsigned fw=0,fh=0;
static void*h;
static unsigned long long asamp;static bool vk_mode;static bool vk_readback(unsigned,unsigned,uint8_t**);
static long frames,shotframes[64]; static int nshots;
static uint8_t*px; static int shots_done;

static double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static void logcb(int lvl,const char*fmt,...){va_list a;va_start(a,fmt);if(getenv("FE_LOG")||lvl>=2){fprintf(stderr,"[core%d] ",lvl);vfprintf(stderr,fmt,a);}va_end(a);}
static void*getproc(const char*n){static void*gl;if(!gl)gl=dlopen("/System/Library/Frameworks/OpenGL.framework/OpenGL",RTLD_LAZY);return dlsym(gl,n);}
static uintptr_t getfbo(void){return fbo;}
static void mkfbo(unsigned w,unsigned h_){
  if(fbo){glDeleteFramebuffers(1,&fbo);glDeleteTextures(1,&tex);glDeleteRenderbuffers(1,&rb);}
  glGenFramebuffers(1,&fbo);glGenTextures(1,&tex);glGenRenderbuffers(1,&rb);
  glBindTexture(GL_TEXTURE_2D,tex);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h_,0,GL_RGBA,GL_UNSIGNED_BYTE,0);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
  glBindRenderbuffer(GL_RENDERBUFFER,rb);glRenderbufferStorage(GL_RENDERBUFFER,GL_DEPTH24_STENCIL8,w,h_);
  glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,tex,0);
  glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_DEPTH_STENCIL_ATTACHMENT,GL_RENDERBUFFER,rb);
  fprintf(stderr,"fbo %ux%u status 0x%x\n",w,h_,glCheckFramebufferStatus(GL_FRAMEBUFFER));fw=w;fh=h_;
}
static void png(const char*path,const uint8_t*rgba,int w,int hh,bool flip){
  FILE*f=fopen(path,"wb");if(!f)return;size_t rl=w*4+1;uint8_t*raw=malloc(rl*hh);
  for(int y=0;y<hh;y++){raw[y*rl]=0;memcpy(raw+y*rl+1,rgba+(size_t)(flip?hh-1-y:y)*w*4,w*4);}
  uLongf cl=compressBound(rl*hh);uint8_t*c=malloc(cl);compress(c,&cl,raw,rl*hh);
  static uint32_t tab[256];if(!tab[1])for(uint32_t n=0;n<256;n++){uint32_t k=n;for(int j=0;j<8;j++)k=k&1?0xedb88320u^(k>>1):k>>1;tab[n]=k;}
  #define W32(v) do{uint32_t x=(v);uint8_t b[4]={x>>24,x>>16,x>>8,x};fwrite(b,1,4,f);}while(0)
  #define CH(t,d,l) do{W32(l);fwrite(t,1,4,f);if(l)fwrite(d,1,l,f);uint32_t cr=~0u;for(int i=0;i<4;i++)cr=tab[(cr^(uint8_t)t[i])&255]^(cr>>8);for(size_t i=0;i<(size_t)(l);i++)cr=tab[(cr^((uint8_t*)d)[i])&255]^(cr>>8);W32(~cr);}while(0)
  fwrite("\x89PNG\r\n\x1a\n",1,8,f);uint8_t ih[13]={w>>24,w>>16,w>>8,w,hh>>24,hh>>16,hh>>8,hh,8,6,0,0,0};
  CH("IHDR",ih,13);CH("IDAT",c,cl);CH("IEND",ih,0);fclose(f);free(raw);free(c);
}
static void video(const void*data,unsigned w,unsigned hh,size_t pitch){
  bool want=false;for(int i=0;i<nshots;i++)if(shotframes[i]==frames)want=true;
  if(!want)return;
  char p[1024];snprintf(p,sizeof p,"%s/shot_%06ld.png",outdir,frames);
  if(vk_mode&&data==(void*)-1){uint8_t*o;if(vk_readback(w,hh,&o))png(p,o,w,hh,false);else{fprintf(stderr,"no image\n");return;}}
  else if(have_hw&&data==(void*)-1){
    if(!px)px=malloc(4096*4096*4);
    glBindFramebuffer(GL_FRAMEBUFFER,fbo);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,w,hh,GL_RGBA,GL_UNSIGNED_BYTE,px);
    png(p,px,w,hh,!hw.bl);
  } else if(data){ // XRGB8888 software
    uint8_t*o=malloc(w*hh*4);for(unsigned y=0;y<hh;y++)for(unsigned x=0;x<w;x++){const uint8_t*s=(const uint8_t*)data+y*pitch+x*4;uint8_t*d=o+(y*w+x)*4;d[0]=s[2];d[1]=s[1];d[2]=s[0];d[3]=255;}
    png(p,o,w,hh,false);free(o);
  }
  fprintf(stderr,"shot %s (%ux%u)\n",p,w,hh);shots_done++;
}

// ---------------- Vulkan (MoltenVK, headless: no surface, no swapchain) ----------------
static void*vkdl; static PFN_vkGetInstanceProcAddr gipa; static PFN_vkGetDeviceProcAddr gdpa;
static struct retro_hw_render_context_negotiation_interface_vulkan neg; static bool have_neg;
static VkInstance vinst; static struct retro_vulkan_context vctx; static struct retro_hw_render_interface_vulkan vif;
static struct retro_vulkan_image vimg; static bool vimg_set; static pthread_mutex_t qmx=PTHREAD_MUTEX_INITIALIZER;
static unsigned long n_setimg,n_setcmd; static uint32_t vsrc_qf;
#define IFN(n) PFN_##n n=(PFN_##n)gipa(vinst,#n)
#define DFN(n) PFN_##n n=(PFN_##n)gdpa(vctx.device,#n)
static VkInstance wrap_ci(void*o,const VkInstanceCreateInfo*ci){
  VkInstanceCreateInfo c=*ci;const char*ex[32];uint32_t n=0;for(;n<ci->enabledExtensionCount&&n<30;n++)ex[n]=ci->ppEnabledExtensionNames[n];
  bool hasp=false;for(uint32_t i=0;i<n;i++)if(!strcmp(ex[i],"VK_KHR_portability_enumeration"))hasp=true;
  (void)hasp;
  PFN_vkCreateInstance f=(PFN_vkCreateInstance)gipa(NULL,"vkCreateInstance");VkInstance i=0;VkResult r=f(&c,NULL,&i);fprintf(stderr,"vkCreateInstance -> %d\n",r);return i;}
static VkDevice wrap_cd(VkPhysicalDevice g,void*o,const VkDeviceCreateInfo*ci){
  PFN_vkCreateDevice f=(PFN_vkCreateDevice)gipa(vinst,"vkCreateDevice");VkDevice d=0;VkResult r=f(g,ci,NULL,&d);fprintf(stderr,"vkCreateDevice -> %d\n",r);return d;}
static void v_setimg(void*h_,const struct retro_vulkan_image*i,uint32_t ns,const VkSemaphore*s,uint32_t qf){vimg=*i;vimg_set=true;vsrc_qf=qf;n_setimg++;}
static uint32_t v_sync(void*h_){return 0;} static uint32_t v_mask(void*h_){return 1;}
static void v_setcmd(void*h_,uint32_t n,const VkCommandBuffer*c){n_setcmd++;}
static void v_wait(void*h_){} static void v_lock(void*h_){pthread_mutex_lock(&qmx);} static void v_unlock(void*h_){pthread_mutex_unlock(&qmx);} static void v_sig(void*h_,VkSemaphore s){}
static bool vk_init(void){
  vkdl=dlopen(getenv("MVK_LIB"),RTLD_NOW);if(!vkdl){fprintf(stderr,"no MoltenVK: %s\n",dlerror());return false;}
  gipa=dlsym(vkdl,"vkGetInstanceProcAddr");
  VkApplicationInfo dflt={VK_STRUCTURE_TYPE_APPLICATION_INFO,0,"fe",1,"fe",1,VK_API_VERSION_1_1};
  const VkApplicationInfo*ai=(have_neg&&neg.get_application_info)?neg.get_application_info():&dflt;if(!ai)ai=&dflt;
  fprintf(stderr,"neg: version=%u create_instance=%p create_device=%p create_device2=%p appinfo api=0x%x\n",neg.interface_version,(void*)neg.create_instance,(void*)neg.create_device,(void*)neg.create_device2,ai->apiVersion);
  if(have_neg&&neg.interface_version>=2&&neg.create_instance)vinst=neg.create_instance(gipa,ai,wrap_ci,NULL);
  else{VkInstanceCreateInfo ci={VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ci.pApplicationInfo=ai;vinst=wrap_ci(NULL,&ci);}
  if(!vinst)return false;
  IFN(vkEnumeratePhysicalDevices);uint32_t n=0;vkEnumeratePhysicalDevices(vinst,&n,NULL);VkPhysicalDevice pd[8];if(n>8)n=8;vkEnumeratePhysicalDevices(vinst,&n,pd);if(!n)return false;
  bool ok=false;
  if(have_neg&&neg.interface_version>=2&&neg.create_device2)ok=neg.create_device2(&vctx,vinst,pd[0],VK_NULL_HANDLE,gipa,wrap_cd,NULL);
  else if(have_neg&&neg.create_device){
    const char*ex[]={"x"};VkPhysicalDeviceFeatures f;memset(&f,0,sizeof f);
    ok=neg.create_device(&vctx,vinst,pd[0],VK_NULL_HANDLE,gipa,ex,0,NULL,0,&f);}
  fprintf(stderr,"core create_device -> %d dev=%p queue=%p qf=%u\n",ok,(void*)vctx.device,(void*)vctx.queue,vctx.queue_family_index);
  if(!ok)return false;
  PFN_vkGetDeviceProcAddr g=(PFN_vkGetDeviceProcAddr)gipa(vinst,"vkGetDeviceProcAddr");gdpa=g;
  vif=(struct retro_hw_render_interface_vulkan){RETRO_HW_RENDER_INTERFACE_VULKAN,RETRO_HW_RENDER_INTERFACE_VULKAN_VERSION,&vif,vinst,vctx.gpu,vctx.device,g,gipa,vctx.queue,vctx.queue_family_index,v_setimg,v_sync,v_mask,v_setcmd,v_wait,v_lock,v_unlock,v_sig};
  return true;}
static uint8_t*vpx;
static bool vk_readback(unsigned w,unsigned hh,uint8_t**out){
  if(!vimg_set)return false;
  IFN(vkGetPhysicalDeviceMemoryProperties);DFN(vkDeviceWaitIdle);DFN(vkCreateBuffer);DFN(vkGetBufferMemoryRequirements);DFN(vkAllocateMemory);DFN(vkBindBufferMemory);DFN(vkMapMemory);
  DFN(vkCreateCommandPool);DFN(vkAllocateCommandBuffers);DFN(vkBeginCommandBuffer);DFN(vkEndCommandBuffer);DFN(vkCmdPipelineBarrier);DFN(vkCmdCopyImageToBuffer);DFN(vkQueueSubmit);DFN(vkQueueWaitIdle);
  DFN(vkFreeMemory);DFN(vkDestroyBuffer);DFN(vkDestroyCommandPool);
  pthread_mutex_lock(&qmx);vkDeviceWaitIdle(vctx.device);
  VkBufferCreateInfo bc={VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,0,0,(VkDeviceSize)w*hh*4,VK_BUFFER_USAGE_TRANSFER_DST_BIT,VK_SHARING_MODE_EXCLUSIVE};VkBuffer b;vkCreateBuffer(vctx.device,&bc,0,&b);
  VkMemoryRequirements mr;vkGetBufferMemoryRequirements(vctx.device,b,&mr);VkPhysicalDeviceMemoryProperties mp;vkGetPhysicalDeviceMemoryProperties(vctx.gpu,&mp);
  uint32_t mt=0;for(uint32_t i=0;i<mp.memoryTypeCount;i++)if((mr.memoryTypeBits>>i&1)&&(mp.memoryTypes[i].propertyFlags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT))==(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)){mt=i;break;}
  VkMemoryAllocateInfo ma={VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,0,mr.size,mt};VkDeviceMemory m;vkAllocateMemory(vctx.device,&ma,0,&m);vkBindBufferMemory(vctx.device,b,m,0);
  VkCommandPoolCreateInfo pc={VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,0,0,vctx.queue_family_index};VkCommandPool pool;vkCreateCommandPool(vctx.device,&pc,0,&pool);
  VkCommandBufferAllocateInfo ca={VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,0,pool,VK_COMMAND_BUFFER_LEVEL_PRIMARY,1};VkCommandBuffer cb;vkAllocateCommandBuffers(vctx.device,&ca,&cb);
  VkCommandBufferBeginInfo bi={VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,0,VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};vkBeginCommandBuffer(cb,&bi);
  VkImageSubresourceRange sr={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
  VkImageMemoryBarrier br={VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,0,VK_ACCESS_MEMORY_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT,vimg.image_layout,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_QUEUE_FAMILY_IGNORED,VK_QUEUE_FAMILY_IGNORED,vimg.create_info.image,sr};
  vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,0,0,0,1,&br);
  VkBufferImageCopy rg={0,0,0,{VK_IMAGE_ASPECT_COLOR_BIT,0,0,1},{0,0,0},{w,hh,1}};vkCmdCopyImageToBuffer(cb,vimg.create_info.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,b,1,&rg);
  br.srcAccessMask=VK_ACCESS_TRANSFER_READ_BIT;br.dstAccessMask=VK_ACCESS_MEMORY_READ_BIT|VK_ACCESS_MEMORY_WRITE_BIT;br.oldLayout=VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;br.newLayout=vimg.image_layout;
  vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,0,0,0,0,0,1,&br);
  vkEndCommandBuffer(cb);VkSubmitInfo si={VK_STRUCTURE_TYPE_SUBMIT_INFO,0,0,0,0,1,&cb};vkQueueSubmit(vctx.queue,1,&si,0);vkQueueWaitIdle(vctx.queue);
  void*p;vkMapMemory(vctx.device,m,0,VK_WHOLE_SIZE,0,&p);if(!vpx)vpx=malloc(4096*4096*4);memcpy(vpx,p,(size_t)w*hh*4);
  if(vimg.create_info.format==VK_FORMAT_B8G8R8A8_UNORM||vimg.create_info.format==VK_FORMAT_B8G8R8A8_SRGB)for(size_t i=0;i<(size_t)w*hh;i++){uint8_t t=vpx[i*4];vpx[i*4]=vpx[i*4+2];vpx[i*4+2]=t;}
  for(size_t i=0;i<(size_t)w*hh;i++)vpx[i*4+3]=255;
  vkDestroyBuffer(vctx.device,b,0);vkFreeMemory(vctx.device,m,0);vkDestroyCommandPool(vctx.device,pool,0);pthread_mutex_unlock(&qmx);
  *out=vpx;return true;}
static void audio1(int16_t l,int16_t r){asamp++;}
static size_t audiob(const int16_t*d,size_t n){asamp+=n;return n;}
static void inpoll(void){}
static int16_t instate(unsigned port,unsigned dev,unsigned idx,unsigned id){return 0;}
static char*vk[64],*vd[64];static int nvars;
static const char*defval(const char*k){for(int i=0;i<nvars;i++)if(!strcmp(vk[i],k))return vd[i];return NULL;}
static bool env(unsigned cmd,void*d){
  switch(cmd){
  case 3:*(bool*)d=true;return true;
  case 9:case 31:case 30:case 19:*(const char**)d=sysdir;return true;
  case 10:return true;
  case 14:{ // SET_HW_RENDER
    struct hwr*r=d;fprintf(stderr,"SET_HW_RENDER type=%u ver=%u.%u depth=%d stencil=%d bl=%d\n",r->type,r->vmaj,r->vmin,r->depth,r->stencil,r->bl);
    if(r->type==6){hw=*r;vk_mode=true;return true;}
    if(r->type!=1&&r->type!=3)return false; // only GL
    r->getfb=getfbo;r->getproc=getproc;hw=*r;have_hw=true;return true;}
  case 15:{struct var*v=d;char k[256];snprintf(k,sizeof k,"OPT_%s",v->key);const char*e=getenv(k);if(!e)e=defval(v->key);v->value=e;if(getenv("FE_LOG"))fprintf(stderr,"GET_VARIABLE %s -> %s\n",v->key,e?e:"(null)");return e!=NULL;}
  case 16:{for(struct var*v=d;v->key;v++){if(getenv("FE_LOG"))fprintf(stderr,"VAR %s = %s\n",v->key,v->value);if(nvars<64){vk[nvars]=strdup(v->key);const char*sc=strstr(v->value,"; ");char*dv=strdup(sc?sc+2:"");char*bar=strchr(dv,'|');if(bar)*bar=0;vd[nvars++]=dv;}}return true;}
  case 0x10000|43:{neg=*(struct retro_hw_render_context_negotiation_interface_vulkan*)d;have_neg=neg.interface_type==0;fprintf(stderr,"NEG type=%d\n",neg.interface_type);return true;}
  case 0x10000|73:return false;
  case 0x10000|41:if(!vk_mode)return false;*(void**)d=&vif;return true;
  case 17:*(bool*)d=false;return true;
  case 18:return true;
  case 27:*(void**)d=(void*)logcb;return true;
  case 52:*(unsigned*)d=0;return true;
  case 56:*(unsigned*)d=1;return true; // preferred: OPENGL (ask GL)
  case 37:case 32:return true;
  case 8:case 11:case 35:return true;
  case 0x10000|44:return false;
  default:if(getenv("FE_LOG"))fprintf(stderr,"env %u unhandled\n",cmd);return false;}
}
#define SYM(n) rf_##n=dlsym(h,"retro_" #n)
static void(*rf_set_environment)(bool(*)(unsigned,void*)),(*rf_set_video_refresh)(void(*)(const void*,unsigned,unsigned,size_t)),(*rf_set_audio_sample)(void(*)(int16_t,int16_t)),(*rf_set_audio_sample_batch)(size_t(*)(const int16_t*,size_t)),(*rf_set_input_poll)(void(*)(void)),(*rf_set_input_state)(int16_t(*)(unsigned,unsigned,unsigned,unsigned)),(*rf_init)(void),(*rf_run)(void),(*rf_get_system_av_info)(struct avinfo*);
static bool(*rf_load_game)(const struct gameinfo*);
int main(int argc,char**argv){
  if(argc<7){fprintf(stderr,"usage\n");return 2;}
  const char*core=argv[1],*content=argv[2];sysdir=argv[3];outdir=argv[4];double secs=atof(argv[5]);
  for(char*t=strtok(argv[6],",");t;t=strtok(0,","))shotframes[nshots++]=atol(t);
  // GL context (offscreen, no window)
  CGLPixelFormatAttribute at[]={kCGLPFAOpenGLProfile,(CGLPixelFormatAttribute)kCGLOGLPVersion_GL4_Core,kCGLPFAAccelerated,kCGLPFAColorSize,(CGLPixelFormatAttribute)24,0};
  CGLPixelFormatObj pf;GLint np;if(CGLChoosePixelFormat(at,&pf,&np)||!pf){fprintf(stderr,"no pixel format\n");return 3;}
  if(CGLCreateContext(pf,0,&ctx)){fprintf(stderr,"no ctx\n");return 3;}CGLSetCurrentContext(ctx);
  fprintf(stderr,"GL: %s | %s\n",glGetString(GL_RENDERER),glGetString(GL_VERSION));
  h=dlopen(core,RTLD_NOW|RTLD_LOCAL);if(!h){fprintf(stderr,"dlopen: %s\n",dlerror());return 4;}
  SYM(set_environment);SYM(set_video_refresh);SYM(set_audio_sample);SYM(set_audio_sample_batch);SYM(set_input_poll);SYM(set_input_state);SYM(init);SYM(run);SYM(get_system_av_info);SYM(load_game);
  rf_set_environment(env);rf_set_video_refresh(video);rf_set_audio_sample(audio1);rf_set_audio_sample_batch(audiob);rf_set_input_poll(inpoll);rf_set_input_state(instate);
  rf_init();
  struct gameinfo gi={content,0,0,0};
  if(!rf_load_game(&gi)){fprintf(stderr,"load_game failed\n");return 5;}
  {size_t(*gms)(unsigned)=dlsym(h,"retro_get_memory_size");void*(*gmd)(unsigned)=dlsym(h,"retro_get_memory_data");for(unsigned i=0;i<5;i++)fprintf(stderr,"MEMORY id=%u size=%zu data=%p\n",i,gms(i),gmd(i));}
  struct avinfo av;rf_get_system_av_info(&av);fprintf(stderr,"av base %ux%u max %ux%u fps %.3f\n",av.g.bw,av.g.bh,av.g.mw,av.g.mh,av.fps);
  if(vk_mode){if(!vk_init()){fprintf(stderr,"vk_init failed\n");return 6;}hw.reset();}
  if(have_hw){mkfbo(av.g.mw,av.g.mh);hw.reset();}
  double t0=now(),last=t0;long lastf=0;
  while(now()-t0<secs){rf_run();frames++;double t=now();if(t-last>=5){fprintf(stderr,"t=%.0fs frames=%ld  last5s fps=%.1f  avg=%.1f\n",t-t0,frames,(frames-lastf)/(t-last),frames/(t-t0));last=t;lastf=frames;}}
  double dt=now()-t0;fprintf(stderr,"DONE frames=%ld wall=%.1f fps=%.2f (%.0f%% of 59.83) shots=%d\n",frames,dt,frames/dt,100*frames/dt/59.83,shots_done);
  fprintf(stderr,"AUDIO samples=%llu => guest %.1fs at %.0f Hz (wall %.1fs): guest/wall = %.2fx\n",asamp,asamp/av.sr,av.sr,dt,asamp/av.sr/dt);_exit(0);
}
