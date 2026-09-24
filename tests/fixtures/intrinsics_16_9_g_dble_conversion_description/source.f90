program i169g_dble_conversion_description
  implicit none
  double precision :: y
  y = dble(-3)
  call require_true('dble converts integer to double value', kind(y) == kind(0.0d0) .and. y == -3.0d0)
  write(*,'(a)') 'INTRINSICS 16.9.G DBLE CONVERSION DESCRIPTION OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_dble_conversion_description
