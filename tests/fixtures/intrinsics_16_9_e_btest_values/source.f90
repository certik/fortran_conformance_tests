program i169e_btest_bits
  implicit none
  logical :: low_bit, high_bit, zero_bit
  integer :: z
  z = bit_size(0)
  low_bit = btest(1, 0)
  high_bit = btest(ibset(0, z - 1), z - 1)
  zero_bit = btest(1, 1)
  call require_true('btest integer i and pos zero one-bit', low_bit)
  call require_true('btest upper valid pos one-bit', high_bit)
  call require_false('btest zero bit false', zero_bit)
  call require_true('btest result default logical', kind(btest(1, 0)) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.E BTEST VALUES OK'
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
end program i169e_btest_bits
