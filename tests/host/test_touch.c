/* test_touch.c: the touch chain of docs/plans/phase-c.md section 2, every pixel of the bottom screen. */
#include <float.h>
#include <stdint.h>

#include "azh_pure.h"
#include "test_main.h"

_Static_assert(FLT_EVAL_METHOD == 0, "the float32 model needs plain float arithmetic (build with -ffp-contract=off)");

static int is_low_row(int y)
{
    return y == 63 || y == 125 || y == 126 || y == 127;
}

static void check_example(int x, int y, int px, int py)
{
    int16_t gotx;
    int16_t goty;

    azh__touch_pointer(x, y, &gotx, &goty);
    check(gotx == px, "pointer x of (%d,%d) is %d, want %d", x, y, gotx, px);
    check(goty == py, "pointer y of (%d,%d) is %d, want %d", x, y, goty, py);
}

void test_touch(void)
{
    int x;
    int y;
    long low_rows = 0;

    for (y = 0; y < 240; y++) {
        for (x = 0; x < 320; x++) {
            int16_t px;
            int16_t py;
            int32_t fx;
            int32_t fy;
            uint16_t gx;
            uint16_t gy;

            azh__touch_pointer(x, y, &px, &py);
            azh__model_frame_pixel(px, py, &fx, &fy);
            azh__model_guest_touch(fx, fy, &gx, &gy);
            check(!(px == 0 && py == 0), "pointer of (%d,%d) is (0,0)", x, y);
            check(fx == x + 40 && fy == y + 240, "frame pixel of (%d,%d) is (%d,%d)", x, y, (int)fx, (int)fy);
            check(gx == x, "guest x of (%d,%d) is %d", x, y, (int)gx);
            check(gy == (is_low_row(y) ? y - 1 : y), "guest y of (%d,%d) is %d", x, y, (int)gy);
            if (gy != y) {
                low_rows++;
            }
        }
    }
    check(low_rows == 4 * 320, "points with guest y = y - 1: %ld, want %d", low_rows, 4 * 320);
    check_example(0, 0, -26132, 68);
    check_example(159, 0, -82, 68);
    check_example(160, 0, 81, 68);
    check_example(319, 0, 26131, 68);
    check_example(0, 63, -26132, 8669);
    check_example(0, 120, -26132, 16451);
    check_example(0, 239, -26132, 32698);
    check_example(319, 239, 26131, 32698);
}
