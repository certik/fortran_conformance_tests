! rule: S16.9.113-003
! covers: ISHFT-positive-left-shift-bits
! covers: ISHFT-negative-right-shift-bits
! covers: ISHFT-zero-shift-preserves-bits
! covers: ISHFT-shifted-out-bits-lost-and-zeros-shifted-in
program i169n_ishft_value_bits
  implicit none
  integer :: checks
  integer :: n, left_in, right_in, stable
  checks = 0
  n = bit_size(0)
  left_in = ibset(ibset(0, 0), 2)
  right_in = ibset(ibset(0, 4), 6)
  stable = ibset(ibset(ibset(0, 0), 3), n - 2)
  call require('ISHFT positive SHIFT moves bits left', &
       same_bits(ishft(left_in, 3), ibset(ibset(0, 3), 5)), checks)
  call require('ISHFT negative SHIFT moves bits right', &
       same_bits(ishft(right_in, -2), ibset(ibset(0, 2), 4)), checks)
  call require('ISHFT zero SHIFT preserves all bits', same_bits(ishft(stable, 0), stable), checks)
  call require('ISHFT shifted-out bits are lost and zeros shifted in', &
       popcnt(ishft(ibset(0, n - 1), 1)) == 0 .and. popcnt(ishft(1, -1)) == 0, checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 N ISHFT VALUE BITS OK'
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
end program i169n_ishft_value_bits
