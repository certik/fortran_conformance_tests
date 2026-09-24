! rule: S19.5.2.3-001
! covers: allocate-pointer-associated pointer-assignment-associated-target pointer-assignment-target-attribute pointer-assignment-allocated-allocatable-target
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_associated_allocate_assignment
  implicit none
  integer, target :: source_target = 211, direct_target = 223, wrong_target = 227
  integer, allocatable, target :: alloc_target
  integer, pointer :: p_alloc, p_from_pointer, source_pointer, p_direct, p_allocatable
  integer :: checks
  checks = 0
  nullify(p_alloc)
  allocate(p_alloc)
  call expect_true(associated(p_alloc), 'allocated pointer becomes associated')
  source_pointer => source_target
  nullify(p_from_pointer)
  p_from_pointer => source_pointer
  call expect_true(associated(p_from_pointer, source_target), 'pointer assignment to associated pointer')
  call expect_equal(p_from_pointer, 211, 'associated pointer assignment value')
  nullify(p_direct)
  p_direct => direct_target
  call expect_true(associated(p_direct, direct_target), 'pointer assignment to TARGET object')
  allocate(alloc_target)
  alloc_target = 239
  nullify(p_allocatable)
  p_allocatable => alloc_target
  call expect_true(associated(p_allocatable), 'pointer assignment to allocated allocatable target')
  call expect_equal(p_allocatable, 239, 'allocated allocatable target value')
  call expect_equal(checks, 6, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 ASSOCIATED ALLOCATE ASSIGNMENT OK'
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
end program pa1952_associated_allocate_assignment
