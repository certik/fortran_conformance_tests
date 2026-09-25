! rule: S18.2.1-001
! covers:
!   iso-c-binding-module-provided
!   required-null-constants-accessible
!   required-kind-and-character-constants-accessible
!   c-pointer-types-accessible
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_required_entities_access
  use, intrinsic :: iso_c_binding, only: c_ptr, c_funptr, c_null_ptr, c_null_funptr, c_associated, c_signed_char, c_short, c_int, c_long, c_long_long, c_size_t, c_int8_t, c_int16_t, c_int32_t, c_int64_t, c_int_least8_t, c_int_least16_t, c_int_least32_t, c_int_least64_t, c_int_fast8_t, c_int_fast16_t, c_int_fast32_t, c_int_fast64_t, c_intmax_t, c_intptr_t, c_ptrdiff_t, c_float, c_double, c_long_double, c_float_complex, c_double_complex, c_long_double_complex, c_bool, c_char, c_null_char, c_alert, c_backspace, c_form_feed, c_new_line, c_carriage_return, c_horizontal_tab, c_vertical_tab
  implicit none
  type(c_ptr) :: p
  type(c_funptr) :: fp
  integer :: module_probe, kind_total, char_total
  integer(c_int) :: checks
  checks = 0_c_int
  p = c_null_ptr
  fp = c_null_funptr
  module_probe = -777
  kind_total = -999
  char_total = -888
  module_probe = c_int
  kind_total = c_signed_char + c_short + c_int + c_long + c_long_long + c_size_t + c_int8_t + c_int16_t + c_int32_t + c_int64_t + c_int_least8_t + c_int_least16_t + c_int_least32_t + c_int_least64_t + c_int_fast8_t + c_int_fast16_t + c_int_fast32_t + c_int_fast64_t + c_intmax_t + c_intptr_t + c_ptrdiff_t + c_float + c_double + c_long_double + c_float_complex + c_double_complex + c_long_double_complex + c_bool + c_char
  char_total = len(c_null_char) + len(c_alert) + len(c_backspace) + len(c_form_feed) + len(c_new_line) + len(c_carriage_return) + len(c_horizontal_tab) + len(c_vertical_tab)
  call expect_logical(module_probe /= -777, .true., 'intrinsic ISO_C_BINDING module provided')
  call expect_logical(c_associated(p), .false., 'C_NULL_PTR accessible')
  call expect_logical(c_associated(fp), .false., 'C_NULL_FUNPTR accessible')
  call expect_logical(kind_total /= -999, .true., 'Table 18.2 constants accessible')
  call expect_int(int(char_total, c_int), 8_c_int, 'Table 18.1 constants accessible')
  call expect_int(checks, 5_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.1 REQUIRED ENTITIES ACCESS OK'

contains
  subroutine expect_int(actual, expected, label)
    integer(c_int), intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(actual, expected, label)
    logical, intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual .neqv. expected) then
      write(*,'(a,1x,a,1x,l1,1x,l1)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine

  function c_loc_target() result(r)
    use, intrinsic :: iso_c_binding, only: c_loc, c_ptr
    type(c_ptr) :: r
    integer(c_int), target, save :: x = 1_c_int
    r = c_loc(x)
  end function
  function c_funloc_target() result(r)
    use, intrinsic :: iso_c_binding, only: c_funloc, c_funptr
    type(c_funptr) :: r
    r = c_funloc(local_target)
  end function
  integer(c_int) function local_target() bind(c)
    local_target = 1_c_int
  end function
end program
