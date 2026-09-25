! rule: S18.1-002
! covers: fortran-subprogram-referenceable-from-c
! evidence: effect
! standard: f2023
! oracle-basis: standard
module iso_c_binding_callback_state
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: marker = -9_c_int
contains
  subroutine mark_from_c() bind(c, name="batch310_mark_from_c")
    marker = 31_c_int
  end subroutine
end module
program iso_c_binding_fortran_called_from_c
  use, intrinsic :: iso_c_binding, only: c_int
  use iso_c_binding_callback_state, only: marker
  implicit none
  interface
    subroutine c_call_fortran_marker() bind(c, name="batch310_call_fortran_marker")
    end subroutine
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  marker = -9_c_int
  call c_call_fortran_marker()
  call expect_int(marker, 31_c_int, 'Fortran subroutine called from C')
  call expect_int(checks, 1_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 FORTRAN CALLED FROM C OK'

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
