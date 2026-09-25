! rule: S18.1-003
! covers: fortran-global-variable-associated-with-c-external
! evidence: effect
! standard: f2023
! oracle-basis: standard
module iso_c_binding_external_global_m
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="batch310_shared_counter") :: shared_counter = -5_c_int
end module
program iso_c_binding_c_external_global
  use, intrinsic :: iso_c_binding, only: c_int
  use iso_c_binding_external_global_m, only: shared_counter
  implicit none
  interface
    subroutine c_store_shared_counter() bind(c, name="batch310_store_shared_counter")
    end subroutine
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  shared_counter = -5_c_int
  call c_store_shared_counter()
  call expect_int(shared_counter, 123_c_int, 'C external linkage variable')
  call expect_int(checks, 1_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C EXTERNAL GLOBAL OK'

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
