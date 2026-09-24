! rule: S16.9.71-004
! covers: digits-result-default-integer-scalar
program i169h_digits_result_characteristics
  implicit none
  integer, parameter :: alt_ik = merge(8, 4, kind(0) /= 8)
  integer(kind=alt_ik) :: values(2)
  integer :: checks
  checks = 0
  values = [1_alt_ik, 2_alt_ik]
  call require('DIGITS result is default integer scalar', &
       kind(digits(values)) == kind(0) .and. size(shape(digits(values))) == 0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS RESULT CHARACTERISTICS OK'
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
end program i169h_digits_result_characteristics
