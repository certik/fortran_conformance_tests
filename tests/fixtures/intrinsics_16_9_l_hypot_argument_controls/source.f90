! rule: S16.9.97-001
! covers: HYPOT-X-real
! covers: HYPOT-Y-real-same-kind-as-X
program i169l_hypot_argument_controls
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: rk = merge(8, 4, kind(0.0) /= 8)
  integer :: checks
  real(kind=rk) :: x, y
  checks = 0
  x = 0.0_rk
  y = 0.0_rk
  call require('HYPOT admits a real X argument', kind(hypot(x, y)) == kind(x), checks)
  call require('HYPOT admits same-kind real Y argument', kind(hypot(x, y)) == kind(y), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HYPOT ARGUMENT CONTROLS OK'
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
end program i169l_hypot_argument_controls
