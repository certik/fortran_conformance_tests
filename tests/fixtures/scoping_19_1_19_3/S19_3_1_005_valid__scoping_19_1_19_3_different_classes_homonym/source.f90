! rule: S19.3.1-005
! covers: different-local-classes-same-spelling
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_different_classes_homonym
  implicit none
  type :: box
    integer :: tag
  end type box
  type(box) :: obj
  integer :: tag, checks
  tag = 99
  obj%tag = 31
  checks = 0
  call expect_equal(obj%tag, 31, 'component tag class')
  call expect_equal(tag, 99, 'ordinary local tag class')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 DIFFERENT CLASSES HOMONYM OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_different_classes_homonym
