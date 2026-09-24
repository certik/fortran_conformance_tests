! rule: S16.9.76-003
! covers: DSHIFTR-boz-converted-as-int-to-other-kind
program i169h_dshiftr_boz_conversion
  implicit none
  integer :: checks
  integer :: i, j, n, r1, r2
  checks = 0
  n = bit_size(0)
  i = 1
  j = shiftl(1, 2)
  r1 = dshiftr(z'03', j, 2)
  r2 = dshiftr(i, z'03', 1)
  call require('dshiftr BOZ converts as INT to other kind', &
       kind(r1) == kind(j) .and. kind(r2) == kind(i) .and. &
       btest(r1, 0) .and. btest(r1, n - 1) .and. btest(r2, 0) .and. btest(r2, n - 1), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTR BOZ CONVERSION OK'
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
end program i169h_dshiftr_boz_conversion
