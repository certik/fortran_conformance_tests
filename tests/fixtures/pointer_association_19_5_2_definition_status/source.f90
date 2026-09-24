! rule: S19.5.2.7-001
! covers: associated-data-pointer-defined-target-value pointer-definition-through-definable-target
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_definition_status
  implicit none
  integer, target :: defined_target = 123, wrong_defined = 456
  integer, target :: definable_target = 5, wrong_definable = 7
  integer, pointer :: reader, writer
  integer :: observed, checks
  checks = 0
  observed = -909
  reader => defined_target
  observed = reader
  call expect_equal(observed, 123, 'associated pointer has target definition status')
  writer => definable_target
  writer = 789
  call expect_equal(definable_target, 789, 'definition through pointer defines target')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 DEFINITION STATUS OK'
contains
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
end program pa1952_definition_status
