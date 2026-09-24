program i169g_dble_result_kind
  implicit none
  integer :: input(2)
  input = [1, 2]
  call require_true('scalar result double precision kind', kind(dble(1)) == kind(0.0d0))
  call require_true('array result double precision kind', kind(dble(input)) == kind(0.0d0) .and. all(shape(dble(input)) == [2]))
  write(*,'(a)') 'INTRINSICS 16.9.G DBLE RESULT KIND OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169g_dble_result_kind
