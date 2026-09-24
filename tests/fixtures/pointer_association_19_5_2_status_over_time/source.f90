! rule: S19.5.2.1-002
! covers: associated-status-over-time disassociated-status-over-time different-own-image-targets
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_status_over_time
  implicit none
  integer, target :: first_target = 11, second_target = 22, wrong_target = 33
  integer, pointer :: p
  integer :: checks
  checks = 0
  nullify(p)
  p => first_target
  call expect_true(associated(p, first_target), 'associated with first target')
  call expect_equal(p, 11, 'first target value')
  p => second_target
  call expect_true(associated(p, second_target), 'associated with second own-image target')
  call expect_equal(p, 22, 'second own-image target value')
  nullify(p)
  call expect_false(associated(p), 'disassociated after nullify')
  call expect_equal(checks, 5, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 STATUS OVER TIME OK'
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
end program pa1952_status_over_time
