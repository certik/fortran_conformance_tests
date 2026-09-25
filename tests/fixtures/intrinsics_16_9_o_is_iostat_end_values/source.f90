program i169o_is_iostat_end_actual
  implicit none
  integer :: end_status
  integer :: ok_status
  integer :: observed_status
  logical :: observed_logical
  call eof_status(end_status)
  call ok_read_status(ok_status)
  observed_status = end_status
  observed_logical = is_iostat_end(end_status)
  call require_true('is_iostat_end accepts integer i from iostat', is_iostat_end(observed_status))
  call require_true('is_iostat_end result default logical scalar', &
      observed_logical .and. kind(is_iostat_end(end_status)) == kind(.false.))
  call require_true('is_iostat_end true for actual end condition', is_iostat_end(end_status))
  call require_true('successful guarded read gives zero iostat', ok_status == 0)
  call require_false('is_iostat_end false for zero non-end status', is_iostat_end(ok_status))
  write(*,'(a)') 'INTRINSICS 16.9.O IS IOSTAT END VALUES OK'
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
  subroutine eof_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: value
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,*) 12345
    rewind(unit)
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    if (stat /= 0 .or. value /= 12345) error stop
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    call require_true('end read leaves sentinel target unchanged', value == -777)
    close(unit)
  end subroutine eof_status
  subroutine ok_read_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: value
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,*) 24680
    rewind(unit)
    value = -777
    if (value /= -777) error stop
    read(unit,*,iostat=stat) value
    call require_true('successful read defines sentinel target', value == 24680)
    close(unit)
  end subroutine ok_read_status
end program i169o_is_iostat_end_actual
