! rule: S18.2.2-003
! covers: c-int-valid-integer-kind
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_int_valid_kind
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: value
  integer(c_int) :: checks
  checks = 0_c_int
  value = -7_c_int
  value = 19_c_int
  call expect_int(kind(0_c_int), c_int, 'direct C_INT kind inquiry')
  call expect_int(value, 19_c_int, 'integer(C_INT) assignment')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C INT VALID KIND OK'

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
