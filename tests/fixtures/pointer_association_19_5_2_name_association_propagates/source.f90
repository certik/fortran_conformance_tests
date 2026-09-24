! rule: S19.5.2.6-001
! covers: name-associated-pointer-status-propagates
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_name_association_propagates
  implicit none
  integer, target :: target = 701
  integer, pointer :: actual
  integer :: checks
  checks = 0
  nullify(actual)
  call change_dummy(actual)
  call expect_true(associated(actual, target), 'name-associated dummy changes actual status')
  call expect_equal(actual, 701, 'name-associated actual target value')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 NAME ASSOCIATION PROPAGATES OK'
contains
  subroutine change_dummy(dummy)
    integer, pointer :: dummy
    dummy => target
  end subroutine
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_false(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (observed) then
      write(*,'(a,1x,a)') 'PA1952-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'PA1952-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program pa1952_name_association_propagates
