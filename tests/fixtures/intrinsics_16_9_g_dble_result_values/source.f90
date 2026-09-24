program i169g_dble_result_values
  implicit none
  integer, parameter :: boz_words = (storage_size(0.0d0) + storage_size(0) - 1) / storage_size(0)
  complex :: z
  integer :: dble_bits(boz_words), real_bits(boz_words)
  z = cmplx(-4.0, 7.0)
  dble_bits = transfer(dble(z'0000000000000001'), dble_bits, boz_words)
  real_bits = transfer(real(z'0000000000000001', kind(0.0d0)), real_bits, boz_words)
  call require_true('integer conversions exact', dble(-3) == -3.0d0 .and. dble(5) == 5.0d0)
  call require_true('real conversions exact', dble(-2.5) == -2.5d0 .and. dble(0.5) == 0.5d0)
  call require_true('complex real part converted', dble(z) == -4.0d0)
  call require_true('boz delegates to real representation', all(dble_bits == real_bits))
  write(*,'(a)') 'INTRINSICS 16.9.G DBLE RESULT VALUES OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_dble_result_values
