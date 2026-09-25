! rule: S18.2.2-011
! covers: c-char-valid-character-kind-branch
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_char_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_char, c_null_char, c_new_line
  implicit none
  interface
    integer(c_int) function c_two_chars(a, b) bind(c, name="batch310_two_chars")
      import c_int, c_char
      character(kind=c_char), value :: a, b
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(c_null_char), c_char, 'C_CHAR direct constant kind inquiry')
  call expect_int(c_two_chars(c_null_char, c_new_line), 10_c_int, 'C_CHAR C escape values')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C CHAR VALID BRANCH OK'

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
