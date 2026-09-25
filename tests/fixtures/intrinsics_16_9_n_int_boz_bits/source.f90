! rule: S16.9.110-005
! covers: INT-boz-bit-sequence-padding-truncation
program i169n_int_boz_bits
  implicit none
  integer, parameter :: ik = merge(8, 4, kind(0) /= 8)
  integer :: checks
  integer :: b6
  integer(kind=ik) :: z15
  checks = 0
  b6 = int(b'0110')
  z15 = int(z'000F', kind=ik)
  call require('INT BOZ low bit sequence is padded or truncated then preserved', &
       btest(b6, 1) .and. btest(b6, 2) .and. popcnt(b6) == 2 .and. &
       btest(z15, 0) .and. btest(z15, 1) .and. btest(z15, 2) .and. btest(z15, 3) .and. &
       popcnt(z15) == 4, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N INT BOZ BITS OK'
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
  logical function same_bits(a, b)
    integer, intent(in) :: a, b
    integer :: k
    same_bits = .true.
    do k = 0, bit_size(a) - 1
      if (btest(a, k) .neqv. btest(b, k)) same_bits = .false.
    end do
  end function same_bits
end program i169n_int_boz_bits
