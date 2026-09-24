! rule: S19.5.1.4-007
! covers: host-derived-type-object-remains-accessible host-derived-type-subobject-remains-accessible
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_host_type_object
  implicit none
  type :: box
    integer :: v
  end type box
  type(box) :: obj
  integer :: observed, checks
  obj%v = 401
  observed = -11
  checks = 0
  call inner()
  call expect_equal(obj%v, 402, 'host object remains accessible')
  call expect_equal(observed, 402, 'host subobject remains accessible')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST TYPE OBJECT OK'
contains
  subroutine inner()
    implicit none
    type :: box
      integer :: v = 499
    end type box
    obj%v = 402
    observed = obj%v
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_type_object
