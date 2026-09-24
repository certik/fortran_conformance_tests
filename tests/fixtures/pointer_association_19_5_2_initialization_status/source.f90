! rule: S19.5.2.2-001
! covers: association-status-changes initialized-disassociated-status initialized-associated-status
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_initialization_status
  implicit none
  integer, target, save :: associated_target = 31, other_target = 47
  integer, pointer :: dis => null()
  integer, pointer :: assoc => associated_target
  integer, pointer :: changing
  integer :: checks
  checks = 0
  call expect_false(associated(dis), 'explicit null initialization disassociated')
  call expect_true(associated(assoc, associated_target), 'explicit target initialization associated')
  changing => associated_target
  call expect_true(associated(changing, associated_target), 'changing pointer first association')
  nullify(changing)
  call expect_false(associated(changing), 'changing pointer after nullify')
  changing => other_target
  call expect_true(associated(changing, other_target), 'changing pointer second association')
  call expect_equal(checks, 5, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 INITIALIZATION STATUS OK'
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
end program pa1952_initialization_status
