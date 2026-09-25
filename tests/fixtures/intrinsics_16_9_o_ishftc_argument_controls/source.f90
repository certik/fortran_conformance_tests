program i169o_ishftc_argument_controls
  implicit none
  integer :: i_value
  integer :: shift_value
  integer :: size_value
  integer :: full_size
  integer :: absent_result
  integer :: explicit_result
  i_value = ibset(ibset(0, 0), 1)
  call require_true('ishftc integer i argument controls bit result', &
      btest(ishftc(i_value, 1, 4), 1) .and. btest(ishftc(i_value, 1, 4), 2))
  shift_value = 1
  call require_true('ishftc integer shift argument controls direction', &
      btest(ishftc(1, shift_value, 4), 1) .and. .not. btest(ishftc(1, shift_value, 4), 3))
  call require_true('ishftc shift magnitude may equal size', btest(ishftc(1, 4, 4), 0))
  size_value = 4
  call require_true('ishftc positive size controls wrap point', btest(ishftc(8, 1, size_value), 0))
  full_size = bit_size(i_value)
  absent_result = ishftc(ibset(0, full_size - 1), 1)
  explicit_result = ishftc(ibset(0, full_size - 1), 1, full_size)
  call require_true('ishftc absent size acts as bit_size', same_bits(absent_result, explicit_result))
  write(*,'(a)') 'INTRINSICS 16.9.O ISHFTC ARGUMENT CONTROLS OK'
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
end program i169o_ishftc_argument_controls
