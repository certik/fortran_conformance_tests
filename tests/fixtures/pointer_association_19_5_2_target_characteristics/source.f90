! rule: S19.5.2.1-003
! covers: associated-pointer-definition-status-is-target deferred-shape-from-target deferred-type-parameters-from-target polymorphic-pointer-dynamic-type-from-target
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_target_characteristics
  implicit none
  type :: base
    integer :: tag
  end type
  type, extends(base) :: child
    integer :: payload
  end type
  integer, target :: scalar_target = 51, scalar_wrong = 62
  integer, target :: array_target(2:4) = [71, 72, 73]
  integer, target :: other_array(1:3) = [81, 82, 83]
  character(len=5), target :: text_target = 'abcde'
  character(len=3), target :: short_text = 'xyz'
  type(child), target :: child_target
  type(base), target :: base_target
  integer, pointer :: p_scalar
  integer, pointer :: p_array(:)
  character(len=:), pointer :: p_text
  class(base), pointer :: p_poly
  integer :: checks
  checks = 0
  child_target%tag = 9
  child_target%payload = 88
  base_target%tag = 6
  p_scalar => scalar_target
  call expect_equal(p_scalar, 51, 'defined target value through data pointer')
  p_array => array_target
  call expect_equal(lbound(p_array, 1), 2, 'deferred shape lower bound')
  call expect_equal(ubound(p_array, 1), 4, 'deferred shape upper bound')
  call expect_equal(p_array(3), 72, 'deferred shape element value')
  p_text => text_target
  call expect_equal(len(p_text), 5, 'deferred character length')
  if (len(p_text) /= 5 .or. p_text /= 'abcde') error stop 'PA1952-FAIL deferred character value'
  checks = checks + 1
  p_poly => child_target
  select type (p_poly)
  type is (child)
    call expect_equal(p_poly%payload, 88, 'polymorphic dynamic type child payload')
  class default
    error stop 'PA1952-FAIL polymorphic dynamic type branch'
  end select
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 TARGET CHARACTERISTICS OK'
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
end program pa1952_target_characteristics
