! rule: S16.9.96-001
! covers: HUGE-X-integer-real-or-enumeration
! covers: HUGE-X-scalar-or-array
program i169l_huge_argument_controls
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  integer :: ia(2)
  real :: ra(2)
  checks = 0
  ia = [1, 2]
  ra = [1.0, 2.0]
  call require('HUGE admits integer and real arguments', &
       huge(ia(1)) > ia(1) .and. huge(ra(1)) > ra(1), checks)
  call require('HUGE scalar result for scalar and array X', &
       size(shape(huge(ia))) == 0 .and. size(shape(huge(ra))) == 0, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L HUGE ARGUMENT CONTROLS OK'
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
end program i169l_huge_argument_controls
