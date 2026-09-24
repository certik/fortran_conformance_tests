! rule: S16.9.71-006
! covers: digits-x-scalar-or-array
program i169h_digits_scalar_array_models
  implicit none
  integer :: checks
  integer :: ia(3)
  real :: ra(2)
  checks = 0
  ia = [3, 5, 7]
  ra = [1.0, 4.0]
  call require('DIGITS scalar and array same kind agree', &
       digits(ia(1)) == digits(ia) .and. digits(ra(1)) == digits(ra), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS SCALAR ARRAY MODELS OK'
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
end program i169h_digits_scalar_array_models
