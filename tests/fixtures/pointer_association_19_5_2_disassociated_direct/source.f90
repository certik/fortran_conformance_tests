! rule: S19.5.2.4-001
! covers: nullify-pointer-disassociated deallocate-pointer-disassociated pointer-assignment-disassociated-pointer
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_disassociated_direct
  implicit none
  integer, target :: nullify_target = 503, dealloc_replacement = 509, assignment_target = 521
  integer, pointer :: p_nullify, p_dealloc, p_assignment, q_null
  integer :: checks
  checks = 0
  p_nullify => nullify_target
  call expect_true(associated(p_nullify), 'nullify precondition associated')
  nullify(p_nullify)
  call expect_false(associated(p_nullify), 'nullify makes pointer disassociated')
  allocate(p_dealloc)
  call expect_true(associated(p_dealloc), 'deallocate precondition associated')
  deallocate(p_dealloc)
  call expect_false(associated(p_dealloc), 'deallocate makes pointer disassociated')
  p_assignment => assignment_target
  nullify(q_null)
  p_assignment => q_null
  call expect_false(associated(p_assignment), 'assignment to disassociated pointer')
  call expect_equal(checks, 5, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 DISASSOCIATED DIRECT OK'
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
end program pa1952_disassociated_direct
