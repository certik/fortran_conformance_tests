program i169e_bit_size_model
  implicit none
  integer, parameter :: ik = selected_int_kind(12)
  integer :: scalar_z
  integer(kind=ik) :: wide_z
  scalar_z = bit_size(0)
  wide_z = bit_size([0_ik, 1_ik])
  call require_true('bit_size scalar integer argument', scalar_z > 0)
  call require_true('bit_size scalar argument gives scalar result', rank(bit_size(0)) == 0)
  call require_true('bit_size array argument scalar result', rank(bit_size([0, 1])) == 0)
  call require_true('bit_size same kind result', &
      kind(bit_size(0_ik)) == ik .and. rank(bit_size(0_ik)) == 0 .and. kind(wide_z) == ik)
  call require_true('bit_size supplies high model position', btest(ibset(0, scalar_z - 1), scalar_z - 1))
  write(*,'(a)') 'INTRINSICS 16.9.E BIT SIZE MODEL OK'
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
end program i169e_bit_size_model
