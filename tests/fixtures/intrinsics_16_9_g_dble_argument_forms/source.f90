program i169g_dble_argument_forms
  implicit none
  integer, parameter :: boz_words = (storage_size(0.0d0) + storage_size(0) - 1) / storage_size(0)
  integer :: boz_bits(boz_words), ref_bits(boz_words)
  complex :: z
  z = cmplx(-4.0, 7.0)
  boz_bits = transfer(dble(z'0000000000000001'), boz_bits, boz_words)
  ref_bits = transfer(real(z'0000000000000001', kind(0.0d0)), ref_bits, boz_words)
  call require_true('all dble argument forms reached', &
       dble(-3) == -3.0d0 .and. dble(-2.5) == -2.5d0 .and. &
       dble(z) == -4.0d0 .and. all(boz_bits == ref_bits))
  write(*,'(a)') 'INTRINSICS 16.9.G DBLE ARGUMENT FORMS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_dble_argument_forms
