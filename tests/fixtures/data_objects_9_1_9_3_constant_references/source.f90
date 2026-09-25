! rule: S9.3-001
! covers: literal-constant-reference named-constant-reference parameter-attribute-source constant-subobject-reference
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_constant_references
  implicit none
  integer, parameter :: k = 81
  character(len=*), parameter :: word = 'ok'
  integer :: stmt_param
  parameter (stmt_param = 5)
  integer, parameter :: arr(3) = [11, 22, 33]
  character(len=*), parameter :: letters = 'abcd'
  integer :: literal_total, checks
  checks = 0
  literal_total = 1 + 2
  call expect_int(literal_total, 3, 'literal constants in value context')
  call expect_int(k, 81, 'named integer constant reference')
  call expect_char(word, 'ok', 'named character constant reference')
  call expect_int(stmt_param + 6, 11, 'PARAMETER statement named constant')
  call expect_int(arr(2), 22, 'constant array element reference')
  call expect_char(letters(2:3), 'bc', 'constant substring reference')
  call expect_int(checks, 6, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS CONSTANT REFERENCES OK'
contains
  subroutine expect_true(ok, label)
    logical, intent(in) :: ok
    character(len=*), intent(in) :: label
    if (.not. ok) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'DATAOBJ-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char(observed, expected, label)
    character(len=*), intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-LEN', label
      error stop
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-CHAR', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program dataobj_constant_references
