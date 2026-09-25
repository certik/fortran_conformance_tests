! rule: S16.9.103-003
! covers: IBITS-extracted-bits-right-adjusted
! covers: IBITS-other-result-bits-zero
! covers: IBITS-zero-len-result-zero
program i169m_ibits_bits
  implicit none
  integer :: seed, r, zlen, z, checks
  checks = 0
  z = bit_size(0)
  seed = 0
  seed = ibset(seed, 2)
  seed = ibset(seed, 4)
  seed = ibset(seed, 5)
  r = ibits(seed, 2, 3)
  zlen = ibits(seed, 2, 0)
  call require('IBITS extracts LEN bits right-adjusted', &
       btest(r, 0) .and. .not. btest(r, 1) .and. btest(r, 2) .and. &
       ibits(ibset(0, z - 1), z - 1, 1) == 1, checks)
  call require('IBITS zeros every other result bit', popcnt(r) == 2 .and. .not. btest(r, 3), checks)
  call require('IBITS zero LEN gives zero with nonzero companion', popcnt(zlen) == 0 .and. popcnt(r) == 2, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IBITS BITS OK'
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
end program i169m_ibits_bits
