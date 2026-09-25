! rule: S16.9.102-003
! covers: IBCLR-clears-selected-bit
! covers: IBCLR-preserves-other-observed-bits
program i169m_ibclr_bits
  implicit none
  integer :: seed, r, z, checks
  checks = 0
  z = bit_size(0)
  seed = 0
  seed = ibset(seed, 0)
  seed = ibset(seed, 1)
  seed = ibset(seed, 3)
  seed = ibset(seed, z - 1)
  r = ibclr(seed, 1)
  call require('IBCLR clears selected bit', .not. btest(r, 1), checks)
  call require('IBCLR preserves other observed bits', &
       btest(r, 0) .and. btest(r, 3) .and. btest(r, z - 1) .and. .not. btest(r, 2), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M IBCLR BITS OK'
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
end program i169m_ibclr_bits
