! rule: S18.1-006
! covers: interoperable-entity-equivalent-c-entity no-actual-c-entity-required
! evidence: effect
! standard: f2023
! oracle-basis: standard
module iso_c_binding_no_partner_m
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="batch310_no_partner_variable") :: no_partner_variable = -2_c_int
contains
  integer(c_int) function no_partner_function(value) bind(c, name="batch310_no_partner_function")
    integer(c_int), value :: value
    no_partner_function = value + no_partner_variable
  end function
end module
program iso_c_binding_equivalent_and_no_partner
  use, intrinsic :: iso_c_binding, only: c_int, c_loc
  use iso_c_binding_no_partner_m, only: no_partner_variable, no_partner_function
  implicit none
  interface
    subroutine c_mutate_address(ptr) bind(c, name="batch310_mutate_address")
      import c_int
      integer(c_int), intent(inout) :: ptr
    end subroutine
  end interface
  integer(c_int), target :: target_value
  integer(c_int) :: checks
  checks = 0_c_int
  target_value = -8_c_int
  no_partner_variable = -2_c_int
  call c_mutate_address(target_value)
  call expect_int(target_value, 64_c_int, 'equivalent C entity through C_LOC-compatible address')
  call expect_int(no_partner_function(19_c_int), 17_c_int, 'BIND(C) entity without actual C partner')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 EQUIVALENT AND NO PARTNER OK'

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
