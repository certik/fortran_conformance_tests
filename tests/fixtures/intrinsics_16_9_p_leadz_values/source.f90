program i169p_leadz_values
  implicit none
  integer :: zero
  integer :: one
  zero = 0
  one = 1
  call require_true('all zero bits return bit size', leadz(zero) == bit_size(zero))
  call require_true('one low bit counts leading zeros', leadz(one) == bit_size(one) - 1)
  call require_true('leftmost one bit has zero leading zeros', &
       leadz(ibset(0, bit_size(0) - 1)) == 0)
  call require_true('all one bits have zero leading zeros', leadz(not(0)) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.P LEADZ VALUES OK'
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
end program i169p_leadz_values
