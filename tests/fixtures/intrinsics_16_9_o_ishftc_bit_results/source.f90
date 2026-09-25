program i169o_ishftc_bit_results
  implicit none
  integer :: positive_value
  integer :: negative_value
  integer :: zero_value
  integer :: wrap_value
  integer :: outside_value
  positive_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc positive shift moves bits left', &
      btest(ishftc(positive_value, 1, 4), 1) .and. btest(ishftc(positive_value, 1, 4), 2) .and. &
      .not. btest(ishftc(positive_value, 1, 4), 3))
  negative_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc negative shift moves bits right', &
      btest(ishftc(negative_value, -1, 4), 0) .and. btest(ishftc(negative_value, -1, 4), 3) .and. &
      .not. btest(ishftc(negative_value, -1, 4), 2))
  zero_value = ibset(ibset(ibset(ibset(0, 0), 2), 4), 6)
  call require_true('ishftc zero shift preserves selected bits', &
      same_bits(ishftc(zero_value, 0, 5), zero_value))
  wrap_value = ibset(0, 3)
  call require_true('ishftc loses no rightmost field bits', btest(ishftc(wrap_value, 1, 4), 0))
  outside_value = ibset(ibset(0, 5), 8)
  call require_true('ishftc leaves outside field bits unaltered', &
      btest(ishftc(outside_value, 1, 4), 5) .and. btest(ishftc(outside_value, 1, 4), 8))
  write(*,'(a)') 'INTRINSICS 16.9.O ISHFTC BIT RESULTS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
  logical function same_bits(lhs, rhs)
    integer, intent(in) :: lhs, rhs
    integer :: pos
    same_bits = .true.
    do pos = 0, bit_size(lhs) - 1
      same_bits = same_bits .and. (btest(lhs, pos) .eqv. btest(rhs, pos))
    end do
  end function same_bits
end program i169o_ishftc_bit_results
