! rule: S19.5.1.5-001
! covers: bind-module-variable-c-linkage linkage-association-program-long
! evidence: effect
! standard: f2023
! oracle-basis: standard
module association_linkage_mod
  use iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c, name="assoc_link_value") :: link_value = 1_c_int
  interface
    subroutine c_set_link_value(v) bind(c, name="assoc_set_link_value")
      import c_int
      integer(c_int), value :: v
    end subroutine c_set_link_value
    integer(c_int) function c_get_link_value() bind(c, name="assoc_get_link_value")
      import c_int
    end function c_get_link_value
  end interface
end module association_linkage_mod
program association_linkage_bind_module
  use iso_c_binding, only: c_int
  use association_linkage_mod, only: link_value, c_set_link_value, c_get_link_value
  implicit none
  integer :: checks
  checks = 0
  link_value = 5_c_int
  call c_set_link_value(42_c_int)
  call expect_equal(int(link_value), 42, 'C write visible through BIND module variable')
  call expect_equal(int(c_get_link_value()), 42, 'C read sees Fortran BIND module variable')
  link_value = 11_c_int
  call c_set_link_value(77_c_int)
  call expect_equal(int(link_value), 77, 'linkage association persists through program execution')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LINKAGE BIND MODULE OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_linkage_bind_module
