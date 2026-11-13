/* test_input.c: validation, the button map, the libretro query, the circle model. */
#include <stdint.h>
#include <string.h>

#include <libretro.h>

#include "azh_pure.h"
#include "test_main.h"

_Static_assert(RETRO_DEVICE_JOYPAD == 1 && RETRO_DEVICE_MOUSE == 2 && RETRO_DEVICE_ANALOG == 5 &&
               RETRO_DEVICE_POINTER == 6, "input.c's device numbers");
_Static_assert(RETRO_DEVICE_ID_JOYPAD_MASK == 256 && RETRO_DEVICE_ID_POINTER_X == 0 && RETRO_DEVICE_ID_POINTER_Y == 1 &&
               RETRO_DEVICE_ID_POINTER_PRESSED == 2, "input.c's id numbers");

static const struct { int bit; unsigned id; } keys[14] = {
    { 0, RETRO_DEVICE_ID_JOYPAD_A }, { 1, RETRO_DEVICE_ID_JOYPAD_B }, { 2, RETRO_DEVICE_ID_JOYPAD_SELECT },
    { 3, RETRO_DEVICE_ID_JOYPAD_START }, { 4, RETRO_DEVICE_ID_JOYPAD_RIGHT }, { 5, RETRO_DEVICE_ID_JOYPAD_LEFT },
    { 6, RETRO_DEVICE_ID_JOYPAD_UP }, { 7, RETRO_DEVICE_ID_JOYPAD_DOWN }, { 8, RETRO_DEVICE_ID_JOYPAD_R },
    { 9, RETRO_DEVICE_ID_JOYPAD_L }, { 10, RETRO_DEVICE_ID_JOYPAD_X }, { 11, RETRO_DEVICE_ID_JOYPAD_Y },
    { 14, RETRO_DEVICE_ID_JOYPAD_L2 }, { 15, RETRO_DEVICE_ID_JOYPAD_R2 },
};

static void rec_set(int32_t r[AZH_INPUT_INTS], int32_t frame, uint32_t buttons)
{
    memset(r, 0, AZH_INPUT_INTS * sizeof r[0]);
    r[AZH_IN_FRAME] = frame;
    r[AZH_IN_BUTTONS] = (int32_t)buttons;
}

static int validates(const int32_t *r, int32_t n, int32_t frames)
{
    char err[160];

    return azh__input_validate(r, n, frames, err, sizeof err);
}

static void test_validation(void)
{
    int32_t r[2 * AZH_INPUT_INTS];
    char err[160];
    int bit;

    rec_set(r, 1, 0);
    check(validates(r, 1, 10) == AZH_OK, "a plain record is valid");
    check(validates(NULL, 0, 10) == AZH_OK, "n 0 with NULL is valid");
    rec_set(r, 0, 0);
    check(validates(r, 1, 10) == AZH_E_ARG, "frame 0");
    rec_set(r, 11, 0);
    check(validates(r, 1, 10) == AZH_E_ARG, "frame past frames");
    rec_set(r, 5, 0);
    rec_set(r + AZH_INPUT_INTS, 4, 0);
    check(azh__input_validate(r, 2, 10, err, sizeof err) == AZH_E_ARG, "decreasing frames");
    check(strstr(err, "record 1") != NULL && strstr(err, "frame") != NULL, "error names record and field: %s", err);
    rec_set(r, 5, 0);
    rec_set(r + AZH_INPUT_INTS, 5, 0);
    check(validates(r, 2, 10) == AZH_OK, "equal frames are valid");
    for (bit = 0; bit < 32; bit++) {
        int allowed = (AZH_BUTTONS_MASK >> bit & 1u) != 0u;

        rec_set(r, 1, 1u << bit);
        check((validates(r, 1, 10) == AZH_OK) == allowed, "button bit %d allowed=%d", bit, allowed);
    }
    rec_set(r, 1, 0);
    r[AZH_IN_TOUCH_DOWN] = 2;
    check(validates(r, 1, 10) == AZH_E_ARG, "touch down 2");
    r[AZH_IN_TOUCH_DOWN] = 1;
    r[AZH_IN_TOUCH_X] = 320;
    check(validates(r, 1, 10) == AZH_E_ARG, "touch x 320");
    r[AZH_IN_TOUCH_X] = 319;
    r[AZH_IN_TOUCH_Y] = 240;
    check(validates(r, 1, 10) == AZH_E_ARG, "touch y 240");
    r[AZH_IN_TOUCH_DOWN] = 0;
    check(validates(r, 1, 10) == AZH_OK, "touch y 240 ignored when up");
    r[AZH_IN_CIRCLE_X] = 32768;
    check(validates(r, 1, 10) == AZH_E_ARG, "circle x 32768");
    r[AZH_IN_CIRCLE_X] = 0;
    r[AZH_IN_CIRCLE_Y] = -32768;
    check(validates(r, 1, 10) == AZH_E_ARG, "circle y -32768");
    check(validates(r, AZH_MAX_INPUTS + 1, 10) == AZH_E_ARG, "n over the maximum");
    check(validates(NULL, 1, 10) == AZH_E_ARG, "NULL records with n 1");
}

static void test_buttons(void)
{
    int32_t r[AZH_INPUT_INTS];
    azh_held h;
    unsigned id;
    int k;

    for (k = 0; k < 14; k++) {
        rec_set(r, 1, 1u << keys[k].bit);
        azh__held_from_record(&h, r);
        for (id = 0; id < 16; id++) {
            int want = (id == keys[k].id);

            check(azh__held_query(&h, 0, RETRO_DEVICE_JOYPAD, 0, id) == want, "bit %d id %u want %d", keys[k].bit,
                  id, want);
        }
        check(azh__held_query(&h, 0, RETRO_DEVICE_JOYPAD, 0, RETRO_DEVICE_ID_JOYPAD_MASK) == (1 << keys[k].id),
              "mask of bit %d", keys[k].bit);
        check(azh__held_query(&h, 1, RETRO_DEVICE_JOYPAD, 0, keys[k].id) == 0, "port 1 is 0");
    }
    rec_set(r, 1, AZH_BUTTONS_MASK);
    azh__held_from_record(&h, r);
    check(azh__held_query(&h, 0, RETRO_DEVICE_JOYPAD, 0, 14) == 0 && azh__held_query(&h, 0, RETRO_DEVICE_JOYPAD, 0, 15) == 0,
          "ids 14 and 15 stay 0 with every button down");
    check(azh__held_query(&h, 0, RETRO_DEVICE_MOUSE, 0, RETRO_DEVICE_ID_MOUSE_LEFT) == 0, "mouse left is 0");
}

static void test_analog_pointer(void)
{
    int32_t r[AZH_INPUT_INTS];
    azh_held h;

    rec_set(r, 1, 0);
    r[AZH_IN_CIRCLE_X] = 1000;
    r[AZH_IN_CIRCLE_Y] = 2000;
    azh__held_from_record(&h, r);
    check(azh__held_query(&h, 0, RETRO_DEVICE_ANALOG, RETRO_DEVICE_INDEX_ANALOG_LEFT, 0) == 1000, "analog x");
    check(azh__held_query(&h, 0, RETRO_DEVICE_ANALOG, RETRO_DEVICE_INDEX_ANALOG_LEFT, 1) == -2000, "analog y is -up");
    check(azh__held_query(&h, 0, RETRO_DEVICE_ANALOG, RETRO_DEVICE_INDEX_ANALOG_RIGHT, 0) == 0, "right stick x 0");
    check(azh__held_query(&h, 0, RETRO_DEVICE_ANALOG, RETRO_DEVICE_INDEX_ANALOG_RIGHT, 1) == 0, "right stick y 0");
    r[AZH_IN_CIRCLE_X] = -32767;
    r[AZH_IN_CIRCLE_Y] = -32767;
    azh__held_from_record(&h, r);
    check(azh__held_query(&h, 0, RETRO_DEVICE_ANALOG, 0, 1) == 32767, "analog y of -32767 up is 32767");
    rec_set(r, 1, 0);
    r[AZH_IN_TOUCH_DOWN] = 1;
    r[AZH_IN_TOUCH_X] = 160;
    r[AZH_IN_TOUCH_Y] = 120;
    azh__held_from_record(&h, r);
    check(azh__held_query(&h, 0, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_PRESSED) == 1, "pointer pressed");
    check(azh__held_query(&h, 0, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_X) == 81, "pointer x of 160");
    check(azh__held_query(&h, 0, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_Y) == 16451, "pointer y of 120");
    check(azh__held_query(&h, 1, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_PRESSED) == 0, "pointer port 1");
    rec_set(r, 1, 0);
    azh__held_from_record(&h, r);
    check(azh__held_query(&h, 0, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_PRESSED) == 0, "pointer released");
    check(azh__held_query(&h, 0, RETRO_DEVICE_POINTER, 0, RETRO_DEVICE_ID_POINTER_X) == 0, "pointer x released");
}

static void test_circle_model(void)
{
    check(azh__model_guest_circle(32767) == 154, "circle 32767");
    check(azh__model_guest_circle(16384) == 77, "circle 16384");
    check(azh__model_guest_circle(-32767) == -154, "circle -32767");
    check(azh__model_guest_circle(0) == 0, "circle 0");
    check(azh__model_guest_circle(-16384) == -77, "circle -16384");
}

/* the --inputs script line: decimal or 0x hex, a leading 0 is decimal, nothing else */
static void test_script_line(void)
{
    int32_t r[AZH_INPUT_INTS];
    static const struct { const char *text; int want; int32_t buttons; } cases[] = {
        { "1 10 0 0 0 0 0", 7, 10 }, { "1 010 0 0 0 0 0", 7, 10 }, { "1 0x10 0 0 0 0 0", 7, 16 },
        { "1 0X1f 0 0 0 0 0", 7, 31 }, { "1,2,0,0,0,0,0", 7, 2 }, { "1\t-5\t0 0 0 0 0\r\n", 7, -5 },
        { "1 0x7fffffff 0 0 0 0 0", 7, INT32_MAX }, { "1 -2147483648 0 0 0 0 0", 7, INT32_MIN },
        { "   \n", 0, 0 }, { "", 0, 0 }, { "1 2 3", 3, 2 },
        { "1 2147483648 0 0 0 0 0", -1, 0 }, { "1 0x80000000 0 0 0 0 0", -1, 0 }, { "1 +5 0 0 0 0 0", -1, 0 },
        { "1 0x 0 0 0 0 0", -1, 0 }, { "1 -0x10 0 0 0 0 0", -1, 0 }, { "1 08 0 0 0 0 0", 7, 8 },
        { "1 1x 0 0 0 0 0", -1, 0 }, { "1 2 3 4 5 6 7 8", -1, 0 }, { "1 abc 0 0 0 0 0", -1, 0 },
        { "1 0xg 0 0 0 0 0", -1, 0 }, { "1 - 0 0 0 0 0", -1, 0 },
    };
    size_t i;

    for (i = 0; i < sizeof cases / sizeof cases[0]; i++) {
        int k;

        memset(r, 0, sizeof r);
        k = azh__script_line(cases[i].text, r);
        check(k == cases[i].want, "script line '%s': got %d, want %d", cases[i].text, k, cases[i].want);
        if (cases[i].want >= 2 && k == cases[i].want) {
            check(r[AZH_IN_BUTTONS] == cases[i].buttons, "script line '%s': buttons %d, want %d", cases[i].text,
                  (int)r[AZH_IN_BUTTONS], (int)cases[i].buttons);
        }
    }
}

void test_input(void)
{
    test_script_line();
    test_validation();
    test_buttons();
    test_analog_pointer();
    test_circle_model();
}
