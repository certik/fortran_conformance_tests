! rule: S16.9.71-005
! covers: digits-integer-model-q
! covers: digits-real-model-p
! covers: digits-same-kind-same-model-value
program i169h_digits_model_values
  implicit none
  integer :: checks
  integer :: i1, i2
  real :: r1, r2
  checks = 0
  i1 = 1; i2 = 12345
  r1 = 1.0; r2 = 16.0
  call require('integer model q is positive', digits(i1) > 0, checks)
  call require('real model p exceeds one', digits(r1) > 1, checks)
  call require('same type and kind use same model digits', &
       digits(i1) == digits(i2) .and. digits(r1) == digits(r2), checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS MODEL VALUES OK'
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
end program i169h_digits_model_values
