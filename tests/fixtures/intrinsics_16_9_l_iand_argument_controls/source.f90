! rule: S16.9.100-001
! covers: IAND-I-integer-or-boz
! covers: IAND-J-integer-or-boz
program i169l_iand_argument_controls
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: j
  checks = 0
  j = int(z'0A')
  call require('IAND accepts integer or BOZ I', &
       btest(iand(z'0F', j), 3) .and. .not. btest(iand(z'0F', j), 2), checks)
  call require('IAND accepts integer or BOZ J', &
       btest(iand(j, z'0F'), 3) .and. .not. btest(iand(j, z'0F'), 2), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IAND ARGUMENT CONTROLS OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_iand_argument_controls
