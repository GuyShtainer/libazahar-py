/* vk.c: headless Vulkan through MoltenVK (no surface, no swapchain, no window), the render interface handed to the
 * core, and the readback of the last presented image.
 *
 * Sync rule for the readback (the core passes no semaphores): lock the queue mutex, wait for the queue to go idle,
 * barrier the image to TRANSFER_SRC, copy to the host buffer, barrier back, submit, wait idle, unlock. */
#include <assert.h>
#ifdef _WIN32
#include "plat/win_compat.h"
#else
#include <dlfcn.h>
#endif
#include <stdlib.h>
#include <string.h>

#include "azh_internal.h"

#ifdef _WIN32
#define MVK_DEFAULT_PATH "vulkan-1.dll"
#else
#define MVK_DEFAULT_PATH "dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
#endif
#define MAX_GPUS 8u

/* ---------- the proc tables, filled once, every entry checked ---------- */

static int missing(const char *name)
{
    assert(name != NULL);
    return azh_fail(AZH_E_VULKAN, "MoltenVK lacks %s", name);
}

static int load_instance_procs(azh_vk *v)
{
    VkInstance i = v->inst;

    assert(v->gipa != NULL);
    assert(i != VK_NULL_HANDLE);
    v->fn.EnumeratePhysicalDevices = (PFN_vkEnumeratePhysicalDevices)v->gipa(i, "vkEnumeratePhysicalDevices");
    if (v->fn.EnumeratePhysicalDevices == NULL) {
        return missing("vkEnumeratePhysicalDevices");
    }
    v->fn.GetPhysicalDeviceMemoryProperties =
        (PFN_vkGetPhysicalDeviceMemoryProperties)v->gipa(i, "vkGetPhysicalDeviceMemoryProperties");
    if (v->fn.GetPhysicalDeviceMemoryProperties == NULL) {
        return missing("vkGetPhysicalDeviceMemoryProperties");
    }
    v->fn.GetDeviceProcAddr = (PFN_vkGetDeviceProcAddr)v->gipa(i, "vkGetDeviceProcAddr");
    if (v->fn.GetDeviceProcAddr == NULL) {
        return missing("vkGetDeviceProcAddr");
    }
    return AZH_OK;
}

static int load_device_memory_procs(azh_vk *v)
{
    assert(v->fn.GetDeviceProcAddr != NULL);
    assert(v->ctx.device != VK_NULL_HANDLE);
    PFN_vkGetDeviceProcAddr g = v->fn.GetDeviceProcAddr;
    VkDevice d = v->ctx.device;

    v->fn.DeviceWaitIdle = (PFN_vkDeviceWaitIdle)g(d, "vkDeviceWaitIdle");
    v->fn.CreateBuffer = (PFN_vkCreateBuffer)g(d, "vkCreateBuffer");
    v->fn.DestroyBuffer = (PFN_vkDestroyBuffer)g(d, "vkDestroyBuffer");
    v->fn.GetBufferMemoryRequirements = (PFN_vkGetBufferMemoryRequirements)g(d, "vkGetBufferMemoryRequirements");
    v->fn.AllocateMemory = (PFN_vkAllocateMemory)g(d, "vkAllocateMemory");
    v->fn.FreeMemory = (PFN_vkFreeMemory)g(d, "vkFreeMemory");
    v->fn.BindBufferMemory = (PFN_vkBindBufferMemory)g(d, "vkBindBufferMemory");
    v->fn.MapMemory = (PFN_vkMapMemory)g(d, "vkMapMemory");
    v->fn.UnmapMemory = (PFN_vkUnmapMemory)g(d, "vkUnmapMemory");
    if (v->fn.DeviceWaitIdle == NULL || v->fn.CreateBuffer == NULL || v->fn.DestroyBuffer == NULL ||
        v->fn.GetBufferMemoryRequirements == NULL || v->fn.AllocateMemory == NULL || v->fn.FreeMemory == NULL ||
        v->fn.BindBufferMemory == NULL || v->fn.MapMemory == NULL || v->fn.UnmapMemory == NULL) {
        return missing("a device memory or buffer function");
    }
    return AZH_OK;
}

static int load_device_command_procs(azh_vk *v)
{
    assert(v->fn.GetDeviceProcAddr != NULL);
    assert(v->ctx.device != VK_NULL_HANDLE);
    PFN_vkGetDeviceProcAddr g = v->fn.GetDeviceProcAddr;
    VkDevice d = v->ctx.device;

    v->fn.CreateCommandPool = (PFN_vkCreateCommandPool)g(d, "vkCreateCommandPool");
    v->fn.DestroyCommandPool = (PFN_vkDestroyCommandPool)g(d, "vkDestroyCommandPool");
    v->fn.AllocateCommandBuffers = (PFN_vkAllocateCommandBuffers)g(d, "vkAllocateCommandBuffers");
    v->fn.ResetCommandBuffer = (PFN_vkResetCommandBuffer)g(d, "vkResetCommandBuffer");
    v->fn.BeginCommandBuffer = (PFN_vkBeginCommandBuffer)g(d, "vkBeginCommandBuffer");
    v->fn.EndCommandBuffer = (PFN_vkEndCommandBuffer)g(d, "vkEndCommandBuffer");
    v->fn.CmdPipelineBarrier = (PFN_vkCmdPipelineBarrier)g(d, "vkCmdPipelineBarrier");
    v->fn.CmdCopyImageToBuffer = (PFN_vkCmdCopyImageToBuffer)g(d, "vkCmdCopyImageToBuffer");
    v->fn.QueueSubmit = (PFN_vkQueueSubmit)g(d, "vkQueueSubmit");
    v->fn.QueueWaitIdle = (PFN_vkQueueWaitIdle)g(d, "vkQueueWaitIdle");
    if (v->fn.CreateCommandPool == NULL || v->fn.DestroyCommandPool == NULL || v->fn.AllocateCommandBuffers == NULL ||
        v->fn.ResetCommandBuffer == NULL || v->fn.BeginCommandBuffer == NULL || v->fn.EndCommandBuffer == NULL ||
        v->fn.CmdPipelineBarrier == NULL || v->fn.CmdCopyImageToBuffer == NULL || v->fn.QueueSubmit == NULL ||
        v->fn.QueueWaitIdle == NULL) {
        return missing("a command buffer or queue function");
    }
    return AZH_OK;
}

/* ---------- the interface callbacks the core calls (handle = the state struct) ---------- */

static void cb_set_image(void *handle, const struct retro_vulkan_image *image, uint32_t num_semaphores,
                         const VkSemaphore *semaphores, uint32_t src_queue_family)
{
    azh_state *s = handle;

    assert(s == &azh_g && image != NULL);
    (void)num_semaphores;     /* the core passes none */
    (void)semaphores;
    s->vk.img = image->create_info.image;     /* copied: the pointer is valid only until the video callback returns */
    s->vk.layout = image->image_layout;
    s->vk.fmt = image->create_info.format;
    s->vk.src_qf = src_queue_family;
    s->vk.img_valid = 1;
}

static uint32_t cb_get_sync_index(void *handle)
{
    (void)handle;
    return 0u;
}

static uint32_t cb_get_sync_index_mask(void *handle)
{
    (void)handle;
    return 1u;
}

static void cb_set_command_buffers(void *handle, uint32_t num_cmd, const VkCommandBuffer *cmd)
{
    (void)handle;     /* the core submits its own work; nothing for the host to do */
    (void)num_cmd;
    (void)cmd;
}

static void cb_wait_sync_index(void *handle)
{
    (void)handle;
}

static void cb_lock_queue(void *handle)
{
    azh_state *s = handle;

    assert(s == &azh_g);
    (void)pthread_mutex_lock(&s->vk.qmx);
}

static void cb_unlock_queue(void *handle)
{
    azh_state *s = handle;

    assert(s == &azh_g);
    (void)pthread_mutex_unlock(&s->vk.qmx);
}

static void cb_set_signal_semaphore(void *handle, VkSemaphore semaphore)
{
    (void)handle;
    (void)semaphore;
}

static void fill_interface(azh_state *s)
{
    azh_vk *v = &s->vk;

    assert(v->inst != VK_NULL_HANDLE && v->ctx.device != VK_NULL_HANDLE);
    assert(v->fn.GetDeviceProcAddr != NULL && v->gipa != NULL);
    v->iface = (struct retro_hw_render_interface_vulkan) {
        .interface_type = RETRO_HW_RENDER_INTERFACE_VULKAN,
        .interface_version = RETRO_HW_RENDER_INTERFACE_VULKAN_VERSION,
        .handle = s,
        .instance = v->inst,
        .gpu = v->ctx.gpu,
        .device = v->ctx.device,
        .get_device_proc_addr = v->fn.GetDeviceProcAddr,
        .get_instance_proc_addr = v->gipa,
        .queue = v->ctx.queue,
        .queue_index = v->ctx.queue_family_index,
        .set_image = cb_set_image,
        .get_sync_index = cb_get_sync_index,
        .get_sync_index_mask = cb_get_sync_index_mask,
        .set_command_buffers = cb_set_command_buffers,
        .wait_sync_index = cb_wait_sync_index,
        .lock_queue = cb_lock_queue,
        .unlock_queue = cb_unlock_queue,
        .set_signal_semaphore = cb_set_signal_semaphore,
    };
}

const struct retro_hw_render_interface_vulkan *azh_vk_iface(void)
{
    return (azh_g.vk_ready != 0) ? &azh_g.vk.iface : NULL;
}

/* ---------- instance and device ---------- */

static int open_loader(azh_vk *v)
{
    const char *path = getenv("LAZ_MVK");

    assert(v != NULL);
    assert(v->dl == NULL);
    if (path == NULL || *path == '\0') {
        path = MVK_DEFAULT_PATH;
    }
#ifdef _WIN32
    v->dl = azh_win_dlopen(path, 1);                 /* the loader comes from system32 only */
#else
    v->dl = dlopen(path, RTLD_NOW | RTLD_LOCAL);
#endif
    if (v->dl == NULL) {
        const char *e = dlerror();

        return azh_fail(AZH_E_VULKAN, "cannot load MoltenVK %s: %s", path, e != NULL ? e : "unknown error");
    }
    v->gipa = (PFN_vkGetInstanceProcAddr)dlsym(v->dl, "vkGetInstanceProcAddr");
    if (v->gipa == NULL) {
        return missing("vkGetInstanceProcAddr");
    }
    v->fn.CreateInstance = (PFN_vkCreateInstance)v->gipa(NULL, "vkCreateInstance");
    if (v->fn.CreateInstance == NULL) {
        return missing("vkCreateInstance");
    }
    return AZH_OK;
}

/* the wrappers a v2 negotiation hands back to us; the opaque pointer is the state struct */
static VkInstance wrap_create_instance(void *opaque, const VkInstanceCreateInfo *ci)
{
    azh_state *s = opaque;
    VkInstance inst = VK_NULL_HANDLE;

    assert(s == &azh_g && ci != NULL);
    if (s->vk.fn.CreateInstance(ci, NULL, &inst) != VK_SUCCESS) {
        return VK_NULL_HANDLE;
    }
    return inst;
}

static VkDevice wrap_create_device(VkPhysicalDevice gpu, void *opaque, const VkDeviceCreateInfo *ci)
{
    azh_state *s = opaque;
    PFN_vkCreateDevice create = (PFN_vkCreateDevice)s->vk.gipa(s->vk.inst, "vkCreateDevice");
    VkDevice dev = VK_NULL_HANDLE;

    assert(s == &azh_g && ci != NULL);
    if (create == NULL || create(gpu, ci, NULL, &dev) != VK_SUCCESS) {
        return VK_NULL_HANDLE;
    }
    return dev;
}

static int make_instance(azh_state *s)
{
    azh_vk *v = &s->vk;
    const struct retro_hw_render_context_negotiation_interface_vulkan *n = &s->neg;
    static const VkApplicationInfo dflt = { .sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .pApplicationName = "azhost",
                                            .apiVersion = VK_API_VERSION_1_1 };
    const VkApplicationInfo *ai = (s->have_neg != 0 && n->get_application_info != NULL) ? n->get_application_info() : NULL;
    VkInstanceCreateInfo ci = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO };

    assert(v->gipa != NULL && v->fn.CreateInstance != NULL);
    assert(v->inst == VK_NULL_HANDLE);
    if (ai == NULL) {
        ai = &dflt;
    }
    azh_log(AZH_LOG_INFO, "negotiation: version %u, create_instance %s, create_device %s, create_device2 %s, "
            "app api 0x%x", s->have_neg != 0 ? n->interface_version : 0u, n->create_instance != NULL ? "yes" : "no",
            n->create_device != NULL ? "yes" : "no", n->create_device2 != NULL ? "yes" : "no", ai->apiVersion);
    if (s->have_neg != 0 && n->interface_version >= 2u && n->create_instance != NULL) {
        v->inst = n->create_instance(v->gipa, ai, wrap_create_instance, s);
    } else {
        ci.pApplicationInfo = ai;
        if (v->fn.CreateInstance(&ci, NULL, &v->inst) != VK_SUCCESS) {
            v->inst = VK_NULL_HANDLE;
        }
    }
    if (v->inst == VK_NULL_HANDLE) {
        return azh_fail(AZH_E_VULKAN, "vkCreateInstance failed (MoltenVK)");
    }
    return load_instance_procs(v);
}

static int make_device(azh_state *s)
{
    azh_vk *v = &s->vk;
    const struct retro_hw_render_context_negotiation_interface_vulkan *n = &s->neg;
    VkPhysicalDevice gpus[MAX_GPUS];
    uint32_t count = MAX_GPUS;
    bool ok = false;

    assert(v->inst != VK_NULL_HANDLE && v->fn.EnumeratePhysicalDevices != NULL);
    assert(v->ctx.device == VK_NULL_HANDLE);
    if (v->fn.EnumeratePhysicalDevices(v->inst, &count, gpus) < 0 || count == 0u) {
        return azh_fail(AZH_E_VULKAN, "no Vulkan physical device");
    }
    memset(&v->ctx, 0, sizeof v->ctx);
    if (s->have_neg != 0 && n->interface_version >= 2u && n->create_device2 != NULL) {
        ok = n->create_device2(&v->ctx, v->inst, gpus[0], VK_NULL_HANDLE, v->gipa, wrap_create_device, s);
    } else if (s->have_neg != 0 && n->create_device != NULL) {
        ok = n->create_device(&v->ctx, v->inst, gpus[0], VK_NULL_HANDLE, v->gipa, NULL, 0, NULL, 0, NULL);
    }
    if (!ok || v->ctx.device == VK_NULL_HANDLE || v->ctx.queue == VK_NULL_HANDLE) {
        return azh_fail(AZH_E_VULKAN, "the core's create_device failed or none was offered");
    }
    azh_log(AZH_LOG_INFO, "vulkan device ready, queue family %u", v->ctx.queue_family_index);
    return AZH_OK;
}

int azh_vk_init(void)
{
    azh_state *s = &azh_g;
    azh_vk *v = &s->vk;
    int rc;

    assert(s->vk_ready == 0 && s->vk.qmx_ready != 0);
    rc = open_loader(v);
    if (rc == AZH_OK) {
        rc = make_instance(s);
    }
    if (rc == AZH_OK) {
        rc = make_device(s);
    }
    if (rc == AZH_OK) {
        rc = load_device_memory_procs(v);
    }
    if (rc == AZH_OK) {
        rc = load_device_command_procs(v);
    }
    if (rc != AZH_OK) {
        return rc;
    }
    v->fn.GetPhysicalDeviceMemoryProperties(v->ctx.gpu, &v->memprops);
    fill_interface(s);
    s->vk_ready = 1;
    return AZH_OK;
}

/* ---------- the readback ---------- */

static void free_readback_buffer(azh_vk *v)
{
    assert(v != NULL);
    assert(v->fn.UnmapMemory != NULL && v->fn.DestroyBuffer != NULL);
    if (v->mapped != NULL) {
        v->fn.UnmapMemory(v->ctx.device, v->mem);
        v->mapped = NULL;
    }
    if (v->buf != VK_NULL_HANDLE) {
        v->fn.DestroyBuffer(v->ctx.device, v->buf, NULL);
        v->buf = VK_NULL_HANDLE;
    }
    if (v->mem != VK_NULL_HANDLE) {
        v->fn.FreeMemory(v->ctx.device, v->mem, NULL);
        v->mem = VK_NULL_HANDLE;
    }
    v->cap = 0;
}

static int pick_memory_type(const azh_vk *v, uint32_t bits, uint32_t *out)
{
    const VkMemoryPropertyFlags want = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
    uint32_t i;

    assert(out != NULL);
    assert(v->memprops.memoryTypeCount <= VK_MAX_MEMORY_TYPES);
    for (i = 0; i < v->memprops.memoryTypeCount; i++) {
        if (((bits >> i) & 1u) != 0u && (v->memprops.memoryTypes[i].propertyFlags & want) == want) {
            *out = i;
            return 0;
        }
    }
    return -1;
}

/* a host-visible buffer of at least bytes, replacing a smaller one (sizes logged) */
static int ensure_buffer(azh_vk *v, VkDeviceSize bytes)
{
    VkBufferCreateInfo bc = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = bytes,
                              .usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE };
    VkMemoryRequirements mr;
    VkMemoryAllocateInfo ma = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO };
    uint32_t type = 0;

    assert(bytes > 0);
    assert(v->fn.CreateBuffer != NULL);
    if (v->cap >= bytes) {
        return AZH_OK;
    }
    azh_log(AZH_LOG_INFO, "readback buffer %llu -> %llu bytes", (unsigned long long)v->cap,
            (unsigned long long)bytes);
    free_readback_buffer(v);
    if (v->fn.CreateBuffer(v->ctx.device, &bc, NULL, &v->buf) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "vkCreateBuffer failed");
    }
    v->fn.GetBufferMemoryRequirements(v->ctx.device, v->buf, &mr);
    if (pick_memory_type(v, mr.memoryTypeBits, &type) != 0) {
        return azh_fail(AZH_E_VULKAN, "no host-visible coherent memory type");
    }
    ma.allocationSize = mr.size;
    ma.memoryTypeIndex = type;
    if (v->fn.AllocateMemory(v->ctx.device, &ma, NULL, &v->mem) != VK_SUCCESS ||
        v->fn.BindBufferMemory(v->ctx.device, v->buf, v->mem, 0) != VK_SUCCESS ||
        v->fn.MapMemory(v->ctx.device, v->mem, 0, VK_WHOLE_SIZE, 0, &v->mapped) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "readback buffer memory failed");
    }
    v->cap = bytes;
    return AZH_OK;
}

static int ensure_commands(azh_vk *v)
{
    VkCommandPoolCreateInfo pc = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                                   .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
                                   .queueFamilyIndex = v->ctx.queue_family_index };
    VkCommandBufferAllocateInfo ca = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                                       .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1 };

    assert(v->fn.CreateCommandPool != NULL);
    assert(v->ctx.device != VK_NULL_HANDLE);
    if (v->pool != VK_NULL_HANDLE) {
        return AZH_OK;
    }
    if (v->fn.CreateCommandPool(v->ctx.device, &pc, NULL, &v->pool) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "vkCreateCommandPool failed");
    }
    ca.commandPool = v->pool;
    if (v->fn.AllocateCommandBuffers(v->ctx.device, &ca, &v->cb) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "vkAllocateCommandBuffers failed");
    }
    return AZH_OK;
}

/* barrier, copy, barrier back; the queue is idle when this runs */
static int record_copy(azh_vk *v, unsigned w, unsigned h)
{
    VkCommandBufferBeginInfo bi = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
                                    .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT };
    VkImageMemoryBarrier br = {
        .sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,
        .dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT, .oldLayout = v->layout,
        .newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, .srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .image = v->img,
        .subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 } };
    VkBufferImageCopy rg = { .imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 },
                             .imageExtent = { w, h, 1 } };

    assert(v->cb != VK_NULL_HANDLE && v->buf != VK_NULL_HANDLE && v->img != VK_NULL_HANDLE);
    assert(w > 0u && h > 0u);
    if (v->fn.ResetCommandBuffer(v->cb, 0) != VK_SUCCESS || v->fn.BeginCommandBuffer(v->cb, &bi) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "cannot begin the readback command buffer");
    }
    v->fn.CmdPipelineBarrier(v->cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0,
                             NULL, 1, &br);
    v->fn.CmdCopyImageToBuffer(v->cb, v->img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, v->buf, 1, &rg);
    br.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    br.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
    br.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    br.newLayout = v->layout;
    v->fn.CmdPipelineBarrier(v->cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, NULL, 0,
                             NULL, 1, &br);
    if (v->fn.EndCommandBuffer(v->cb) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "vkEndCommandBuffer failed");
    }
    return AZH_OK;
}

/* mapped bytes to RGBA with alpha 255; B8G8R8A8 is swapped, any other format was refused earlier */
static void convert(azh_vk *v, size_t pixels, int swap)
{
    const uint8_t *src = v->mapped;
    uint8_t *dst = v->rgba;
    size_t i;

    assert(src != NULL && dst != NULL);
    assert(pixels * 4u <= v->rgba_cap && (VkDeviceSize)pixels * 4u <= v->cap);
    for (i = 0; i < pixels; i++) {
        dst[0] = swap != 0 ? src[2] : src[0];
        dst[1] = src[1];
        dst[2] = swap != 0 ? src[0] : src[2];
        dst[3] = 255u;
        src += 4;
        dst += 4;
    }
}

static int format_swap(VkFormat f, int *swap)
{
    assert(swap != NULL);
    assert(f >= 0);
    if (f == VK_FORMAT_R8G8B8A8_UNORM || f == VK_FORMAT_R8G8B8A8_SRGB) {
        *swap = 0;
        return 0;
    }
    if (f == VK_FORMAT_B8G8R8A8_UNORM || f == VK_FORMAT_B8G8R8A8_SRGB) {
        *swap = 1;
        return 0;
    }
    return -1;
}

static int ensure_rgba(azh_vk *v, size_t bytes)
{
    uint8_t *p;

    assert(bytes > 0);
    assert(v != NULL);
    if (v->rgba_cap >= bytes) {
        return AZH_OK;
    }
    p = realloc(v->rgba, bytes);
    if (p == NULL) {
        return azh_fail(AZH_E_NOMEM, "out of memory for a %zu byte frame", bytes);
    }
    v->rgba = p;
    v->rgba_cap = bytes;
    return AZH_OK;
}

/* the submit-wait-convert part, called with the queue mutex held */
static int submit_and_convert(azh_vk *v, size_t pixels, int swap)
{
    VkSubmitInfo si = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO, .commandBufferCount = 1, .pCommandBuffers = &v->cb };

    assert(pixels > 0);
    assert(swap == 0 || swap == 1);
    if (v->fn.QueueSubmit(v->ctx.queue, 1, &si, VK_NULL_HANDLE) != VK_SUCCESS ||
        v->fn.QueueWaitIdle(v->ctx.queue) != VK_SUCCESS) {
        return azh_fail(AZH_E_VULKAN, "readback submit failed");
    }
    convert(v, pixels, swap);
    return AZH_OK;
}

int azh_vk_readback(unsigned w, unsigned h, const uint8_t **out)
{
    azh_vk *v = &azh_g.vk;
    size_t pixels = (size_t)w * h;
    int swap = 0;
    int rc;

    assert(out != NULL && azh_g.vk_ready != 0);
    if (v->img_valid == 0 || w == 0u || h == 0u) {
        return azh_fail(AZH_E_VULKAN, "no image has been presented yet");
    }
    if (format_swap(v->fmt, &swap) != 0) {
        return azh_fail(AZH_E_VULKAN, "unsupported image format %d (only R8G8B8A8 and B8G8R8A8)", (int)v->fmt);
    }
    (void)pthread_mutex_lock(&v->qmx);
    rc = (v->fn.DeviceWaitIdle(v->ctx.device) == VK_SUCCESS) ? AZH_OK : azh_fail(AZH_E_VULKAN, "vkDeviceWaitIdle failed");
    if (rc == AZH_OK) {
        rc = ensure_buffer(v, (VkDeviceSize)pixels * 4u);
    }
    if (rc == AZH_OK) {
        rc = ensure_commands(v);
    }
    if (rc == AZH_OK) {
        rc = ensure_rgba(v, pixels * 4u);
    }
    if (rc == AZH_OK) {
        rc = record_copy(v, w, h);
    }
    if (rc == AZH_OK) {
        rc = submit_and_convert(v, pixels, swap);
    }
    (void)pthread_mutex_unlock(&v->qmx);
    if (rc == AZH_OK) {
        *out = v->rgba;
    }
    return rc;
}

void azh_vk_close(void)
{
    azh_vk *v = &azh_g.vk;

    if (azh_g.vk_ready != 0) {
        (void)pthread_mutex_lock(&v->qmx);
        if (v->fn.DeviceWaitIdle != NULL) {
            (void)v->fn.DeviceWaitIdle(v->ctx.device);
        }
        free_readback_buffer(v);
        if (v->pool != VK_NULL_HANDLE) {
            v->fn.DestroyCommandPool(v->ctx.device, v->pool, NULL);
            v->pool = VK_NULL_HANDLE;
        }
        (void)pthread_mutex_unlock(&v->qmx);
        azh_g.vk_ready = 0;
    }
    free(v->rgba);
    v->rgba = NULL;
    v->rgba_cap = 0;
    /* the core's device and instance, and MoltenVK itself, are left to process exit: they belong to threads the core owns */
}
