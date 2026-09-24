! rule: S16.9.98-001
! covers: IACHAR-C-character-length-one
! covers: IACHAR-KIND-scalar-integer-constant-expression
program i169l_iachar_argument_controls
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  checks = 0
  call require('IACHAR admits length-one character C', iachar('A') == 65, checks)
  call require('IACHAR admits scalar integer constant KIND', &
       kind(iachar('B', kind=ik)) == ik .and. iachar('B', kind=ik) == 66_ik, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IACHAR ARGUMENT CONTROLS OK'
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
end program i169l_iachar_argument_controls
