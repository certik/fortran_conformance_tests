! rule: S16.9.77-005
! covers: EOSHIFT-DIM-absent-defaults-to-one
program i169h_eoshift_dim_default
  implicit none
  integer :: checks
  integer :: a(2,3)
  checks = 0
  a = reshape([1, 2, 3, 4, 5, 6], [2, 3])
  call require('EOSHIFT absent DIM defaults to one', &
       all(eoshift(a, 1) == eoshift(a, 1, dim=1)) .and. any(eoshift(a, 1) /= eoshift(a, 1, dim=2)), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT DIM DEFAULT OK'
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
end program i169h_eoshift_dim_default
