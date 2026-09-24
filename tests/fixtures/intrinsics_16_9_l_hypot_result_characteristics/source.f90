! rule: S16.9.97-002
! covers: HYPOT-result-same-real-kind-as-X
program i169l_hypot_result_characteristics
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
  call require('HYPOT result has same kind as X', kind(hypot(x, y)) == kind(x), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HYPOT RESULT CHARACTERISTICS OK'
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
end program i169l_hypot_result_characteristics
