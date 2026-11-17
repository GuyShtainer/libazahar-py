/* pins.h: the core versions this host accepts (docs/PLAN.md 2.4). Change only together with tools/fetch.sh. */
#ifndef AZH_PINS_H
#define AZH_PINS_H

#define AZH_STOCK_VERSION "2126.2"
/* Azahar's own CI builds of that tag (the official Windows libretro core) name themselves by the pinned commit's
   short hash (core/PIN AZAHAR_COMMIT), so the stock core may also report this; no suffixes ever follow it */
#define AZH_STOCK_COMMIT "219d743"
/* our core's suffixes: lazpy.1 (the first core, never released) and lazpy.2 (adds lazpy_threads); the text is for messages */
#define AZH_LAZPY_SUFFIXES { "-lazpy.1", "-lazpy.2" }
#define AZH_LAZPY_SUFFIX_TEXT "-lazpy.1 or -lazpy.2"

#endif
