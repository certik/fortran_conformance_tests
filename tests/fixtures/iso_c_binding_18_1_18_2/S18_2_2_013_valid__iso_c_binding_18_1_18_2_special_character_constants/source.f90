! rule: S18.2.2-013
! covers:
!   c-special-character-named-constants
!   c-special-character-length-one
!   c-special-character-kind-branch
!   c-special-character-table-values
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_special_character_constants
  use, intrinsic :: iso_c_binding, only: c_int, c_char, c_null_char, c_alert, c_backspace, c_form_feed, c_new_line, c_carriage_return, c_horizontal_tab, c_vertical_tab
  implicit none
  interface
    integer(c_int) function c_check_chars(nul, alert, back, form, newline, carriage, tab, vertical) bind(c, name="batch310_check_chars")
      import c_int, c_char
      character(kind=c_char), value :: nul, alert, back, form, newline, carriage, tab, vertical
    end function
  end interface
  character(kind=kind(c_null_char), len=1) :: holder
  integer(c_int) :: checks
  checks = 0_c_int
  holder = '#'
  holder = c_null_char
  call expect_logical(holder == c_null_char, .true., 'C_NULL_CHAR named constant assignment')
  call expect_int(len(c_null_char), 1_c_int, 'C_NULL_CHAR length one')
  call expect_int(len(c_alert), 1_c_int, 'C_ALERT length one')
  call expect_int(len(c_backspace), 1_c_int, 'C_BACKSPACE length one')
  call expect_int(len(c_form_feed), 1_c_int, 'C_FORM_FEED length one')
  call expect_int(len(c_new_line), 1_c_int, 'C_NEW_LINE length one')
  call expect_int(len(c_carriage_return), 1_c_int, 'C_CARRIAGE_RETURN length one')
  call expect_int(len(c_horizontal_tab), 1_c_int, 'C_HORIZONTAL_TAB length one')
  call expect_int(len(c_vertical_tab), 1_c_int, 'C_VERTICAL_TAB length one')
  call expect_int(kind(c_null_char), c_char, 'C special character kind branch')
  call expect_int(c_check_chars(c_null_char, c_alert, c_backspace, c_form_feed, c_new_line, c_carriage_return, c_horizontal_tab, c_vertical_tab), 8_c_int, 'C special character table values')
  call expect_int(checks, 11_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 SPECIAL CHARACTER CONSTANTS OK'

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
end program
