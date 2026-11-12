/* azh_internal.h: the one state struct and the prototypes shared by the host's files. Everything else is file-static.
 *
 * Function-pointer exception (C golden rule 9, documented): function pointers appear only for (1) the libretro
 * callbacks and the core's retro_* table, (2) the Vulkan interface callbacks, (3) the two Vulkan proc tables. */
#ifndef AZH_INTERNAL_H
#define AZH_INTERNAL_H

#include <pthread.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

#define VK_NO_PROTOTYPES
#include <libretro.h>
#include <libretro_vulkan.h>

#include "azh_pure.h"
#include "azhost.h"

/* ---- host.map layout (hostmap.c) ---- */
#define AZH_MAP_HEADER 4096u
#define AZH_MAP_PX_SIZE (400u * 240u * 4u + 320u * 240u * 4u)      /* top RGBA, then bottom RGBA: 691,200 */
#define AZH_MAP_SIZE (AZH_MAP_HEADER + AZH_MAP_PX_SIZE)            /* 695,296 */
#define AZH_MAP_OFF_HEARTBEAT 16u
#define AZH_MAP_OFF_STOP 24u
#define AZH_MAP_OFF_MSGLEN 28u
#define AZH_MAP_OFF_MSG 32u
#define AZH_MAP_MSG_MAX 1024u
#define AZH_MAP_OFF_SIZES 1056u
#define AZH_MAP_OFF_PXFRAME 1072u

/* ---- log levels (same numbers as retro_log_level) ---- */
enum { AZH_LOG_DEBUG = 0, AZH_LOG_INFO = 1, AZH_LOG_WARN = 2, AZH_LOG_ERROR = 3 };

/* ---- call phases ---- */
enum { AZH_PH_NONE = 0, AZH_PH_OPEN = 1, AZH_PH_BOOTED = 2, AZH_PH_DEAD = 3 /* boot failed: only close works */ };

#define AZH_MAX_OPTS 128
#define AZH_OPT_KEY_MAX 64
#define AZH_OPT_VAL_MAX 128
#define AZH_SEEN_MAX 64
#define AZH_MSG_MAX 1024

typedef struct {
    char key[AZH_OPT_KEY_MAX];
    char *allowed;                  /* "a|b|c" copied from the core's "desc; a|b|c" (owned) */
    char value[AZH_OPT_VAL_MAX];    /* meaningful only when is_set */
    int is_set;
    int warned;
} azh_opt;

/* the 25 symbols of libretro.osx.def */
typedef struct {
    void *dl;
    unsigned (*api_version)(void);
    void (*set_environment)(retro_environment_t);
    void (*set_video_refresh)(retro_video_refresh_t);
    void (*set_audio_sample)(retro_audio_sample_t);
    void (*set_audio_sample_batch)(retro_audio_sample_batch_t);
    void (*set_input_poll)(retro_input_poll_t);
    void (*set_input_state)(retro_input_state_t);
    void (*init)(void);
    void (*deinit)(void);
    void (*get_system_info)(struct retro_system_info *);
    void (*get_system_av_info)(struct retro_system_av_info *);
    void (*set_controller_port_device)(unsigned, unsigned);
    void (*reset)(void);
    void (*run)(void);
    size_t (*serialize_size)(void);
    bool (*serialize)(void *, size_t);
    bool (*unserialize)(const void *, size_t);
    void (*cheat_reset)(void);
    void (*cheat_set)(unsigned, bool, const char *);
    bool (*load_game)(const struct retro_game_info *);
    bool (*load_game_special)(unsigned, const struct retro_game_info *, size_t);
    void (*unload_game)(void);
    unsigned (*get_region)(void);
    void *(*get_memory_data)(unsigned);
    size_t (*get_memory_size)(unsigned);
} azh_core;

/* Vulkan procs, assigned one by one in vk.c (no token pasting) */
typedef struct {
    PFN_vkCreateInstance CreateInstance;
    PFN_vkEnumeratePhysicalDevices EnumeratePhysicalDevices;
    PFN_vkGetPhysicalDeviceMemoryProperties GetPhysicalDeviceMemoryProperties;
    PFN_vkGetDeviceProcAddr GetDeviceProcAddr;
    PFN_vkDeviceWaitIdle DeviceWaitIdle;
    PFN_vkCreateBuffer CreateBuffer;
    PFN_vkDestroyBuffer DestroyBuffer;
    PFN_vkGetBufferMemoryRequirements GetBufferMemoryRequirements;
    PFN_vkAllocateMemory AllocateMemory;
    PFN_vkFreeMemory FreeMemory;
    PFN_vkBindBufferMemory BindBufferMemory;
    PFN_vkMapMemory MapMemory;
    PFN_vkUnmapMemory UnmapMemory;
    PFN_vkCreateCommandPool CreateCommandPool;
    PFN_vkDestroyCommandPool DestroyCommandPool;
    PFN_vkAllocateCommandBuffers AllocateCommandBuffers;
    PFN_vkResetCommandBuffer ResetCommandBuffer;
    PFN_vkBeginCommandBuffer BeginCommandBuffer;
    PFN_vkEndCommandBuffer EndCommandBuffer;
    PFN_vkCmdPipelineBarrier CmdPipelineBarrier;
    PFN_vkCmdCopyImageToBuffer CmdCopyImageToBuffer;
    PFN_vkQueueSubmit QueueSubmit;
    PFN_vkQueueWaitIdle QueueWaitIdle;
} azh_vkfn;

typedef struct {
    void *dl;                                   /* MoltenVK; never dlclosed (it owns threads) */
    PFN_vkGetInstanceProcAddr gipa;
    azh_vkfn fn;
    VkInstance inst;
    struct retro_vulkan_context ctx;
    struct retro_hw_render_interface_vulkan iface;
    pthread_mutex_t qmx;
    int qmx_ready;
    /* the last image the core presented (copied by set_image, never the pointer) */
    int img_valid;
    VkImage img;
    VkImageLayout layout;
    VkFormat fmt;
    uint32_t src_qf;
    /* readback resources, sized from the first HW frame and grown when a frame is larger */
    VkBuffer buf;
    VkDeviceMemory mem;
    VkDeviceSize cap;
    void *mapped;
    VkCommandPool pool;
    VkCommandBuffer cb;
    uint8_t *rgba;
    size_t rgba_cap;
    VkPhysicalDeviceMemoryProperties memprops;
} azh_vk;

typedef struct {
    int phase;
    azh_core core;
    char core_path[AZH_PATH_MAX];
    char sysdir[AZH_PATH_MAX];
    char core_name[64];
    char core_version[128];
    int is_lazpy;
    int core_inited;
    int game_loaded;
    int vk_ready;
    /* boot failure detection */
    int in_reset;                               /* context_reset is running */
    int boot_failed;
    char last_msg[AZH_MSG_MAX];                 /* last SET_MESSAGE text */
    /* frames */
    int64_t abs_frames;                         /* retro_run calls since boot */
    int first_run_done;
    double t_boot;
    int cb_calls;                               /* video callbacks during the current retro_run */
    int cb_null;                                /* the last video callback carried no frame */
    int frame_kind;                             /* 0 none, 1 HW image (Vulkan), 2 software copy */
    unsigned fw, fh;
    uint8_t *sw;
    size_t sw_cap;
    /* libretro state */
    struct retro_hw_render_callback hw;
    int have_hw;
    struct retro_hw_render_context_negotiation_interface_vulkan neg;
    int have_neg;
    struct retro_system_av_info av;
    int mm_logged;
    unsigned seen[AZH_SEEN_MAX];
    int n_seen;
    int n_unset_warned;
    azh_opt opts[AZH_MAX_OPTS];
    int n_opts;
    azh_vk vk;
} azh_state;

extern azh_state azh_g;

/* error text (api.c) */
int azh_fail(int code, const char *fmt, ...) __attribute__((format(printf, 2, 3)));

/* log.c */
int azh_log_open(const char *path);
void azh_log_close(void);
void azh_log(int level, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
void azh_core_log(enum retro_log_level level, const char *fmt, ...);

/* hostmap.c */
int azh_map_create(const char *path);
void azh_map_close(void);
void azh_map_heartbeat(void);
void azh_map_set_stop(int32_t code);
void azh_map_set_message(const char *msg);

/* options.c */
void azh_opts_register(const struct retro_variable *vars);
int azh_opts_set(const char *key, const char *value);
int azh_opts_get(struct retro_variable *var);
void azh_opts_log(void);
void azh_opts_free(void);

/* core.c */
int azh_core_open(const char *path);
void azh_core_install_callbacks(void);
void azh_core_close(void);

/* env.c */
bool azh_env(unsigned cmd, void *data);

/* frame.c */
void azh_video_cb(const void *data, unsigned w, unsigned h, size_t pitch);
void azh_audio_sample_cb(int16_t l, int16_t r);
size_t azh_audio_batch_cb(const int16_t *data, size_t frames);
void azh_input_poll_cb(void);
int16_t azh_input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id);
int azh_frame_write(int32_t screens, const char *prefix);
void azh_frame_free(void);

/* vk.c */
int azh_vk_init(void);
int azh_vk_readback(unsigned w, unsigned h, const uint8_t **out);
void azh_vk_close(void);
const struct retro_hw_render_interface_vulkan *azh_vk_iface(void);

/* run.c */
int azh_run_batch(const azh_batch *b, azh_result *out);

#endif
