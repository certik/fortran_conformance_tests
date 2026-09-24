! rule: S19.5.2.1-001
! covers: pointer-reference-reads-target pointer-reference-defines-target
! evidence: effect
! standard: f2023
! oracle-basis: standard
program pa1952_reference_general
  implicit none
  integer, target :: read_target = 42, wrong_read_target = 64
  integer, target :: write_target = 1, wrong_write_target = 5
  integer, pointer :: reader, writer
  integer :: observed, checks
  checks = 0
  observed = -777
  reader => read_target
  observed = reader
  call expect_equal(observed, 42, 'pointer reference reads target')
  writer => write_target
  writer = 77
  call expect_equal(write_target, 77, 'pointer reference defines target')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'POINTER ASSOCIATION 19.5.2 REFERENCE GENERAL OK'
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
end program pa1952_reference_general
