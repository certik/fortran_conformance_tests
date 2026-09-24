! rule: S19.5.2.3-001
! covers: source-allocate-associated-pointer-subobject dummy-pointer-nonpointer-actual-associated
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_associated_source_dummy
  implicit none
  type :: box
    integer, pointer :: p
  end type
  integer, target :: source_target = 307, dummy_target = 311, other_target = 313
  type(box) :: src
  type(box), allocatable :: dst
  integer :: checks
  checks = 0
  src%p => source_target
  allocate(dst, source=src)
  call expect_true(associated(dst%p, source_target), 'SOURCE associated pointer subobject')
  call expect_equal(dst%p, 307, 'SOURCE associated subobject value')
  call check_dummy(dummy_target)
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 ASSOCIATED SOURCE DUMMY OK'
contains
  subroutine check_dummy(dummy)
    integer, pointer, intent(in) :: dummy
    call expect_true(associated(dummy, dummy_target), 'pointer dummy associated with nonpointer actual')
    call expect_equal(dummy, 311, 'pointer dummy actual value')
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
end program pa1952_associated_source_dummy
