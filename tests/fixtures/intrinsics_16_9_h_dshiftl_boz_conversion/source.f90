! rule: S16.9.75-003
! covers: DSHIFTL-boz-converted-as-int-to-other-kind
program i169h_dshiftl_boz_conversion
  implicit none
  integer :: checks
  integer :: i, j, n, r1, r2
  checks = 0
  n = bit_size(0)
  i = 1
  j = ior(shiftl(1, n - 1), 1)
  r1 = dshiftl(z'03', j, 2)
  r2 = dshiftl(i, z'03', n - 1)
  call require('dshiftl BOZ converts as INT to other kind', &
       kind(r1) == kind(j) .and. kind(r2) == kind(i) .and. &
       btest(r1, 3) .and. btest(r1, 2) .and. btest(r2, 0) .and. btest(r2, n - 1), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTL BOZ CONVERSION OK'
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
end program i169h_dshiftl_boz_conversion
