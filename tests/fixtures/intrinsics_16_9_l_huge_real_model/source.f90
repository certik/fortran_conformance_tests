! rule: S16.9.96-004
! covers: HUGE-real-model-largest-value
! covers: HUGE-real-distinguishes-kinds
program i169l_huge_real_model
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer, parameter :: rk = merge(8, 4, kind(0.0) /= 8)
  integer :: checks
  real(kind=rk) :: x
  checks = 0
  x = 1.0_rk
  call require('HUGE real exponent and fraction match model', &
       exponent(huge(0.0)) == maxexponent(0.0) .and. &
       fraction(huge(0.0)) == 1.0 - scale(1.0, -digits(0.0)), checks)
  call require('HUGE real model distinguishes selected kinds', &
       maxexponent(x) /= maxexponent(0.0) .and. &
       exponent(huge(x)) == maxexponent(x) .and. &
       fraction(huge(x)) == 1.0_rk - scale(1.0_rk, -digits(x)), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HUGE REAL MODEL OK'
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
end program i169l_huge_real_model
