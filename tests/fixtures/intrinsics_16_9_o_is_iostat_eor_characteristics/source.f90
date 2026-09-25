program i169o_is_iostat_eor_actual
  implicit none
  integer :: eor_status
  integer :: ok_status
  integer :: observed_status
  logical :: observed_logical
  call eor_read_status(eor_status)
  call ok_nonadvance_status(ok_status)
  observed_status = eor_status
  observed_logical = is_iostat_eor(eor_status)
  call require_true('is_iostat_eor accepts integer i from iostat', is_iostat_eor(observed_status))
  call require_true('is_iostat_eor result default logical scalar', &
      observed_logical .and. kind(is_iostat_eor(eor_status)) == kind(.false.))
  call require_true('is_iostat_eor true for actual end of record condition', is_iostat_eor(eor_status))
  call require_true('initial nonadvancing read gives zero iostat', ok_status == 0)
  call require_false('is_iostat_eor false for zero non-eor status', is_iostat_eor(ok_status))
  write(*,'(a)') 'INTRINSICS 16.9.O IS IOSTAT EOR CHARACTERISTICS OK'
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
  subroutine eor_read_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: amount
    character(len=3) :: chunk
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,'(a)') 'ABCDE'
    rewind(unit)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('first nonadvancing read fills target', stat == 0 .and. chunk == 'ABC' .and. amount == 3)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('eor read reports available characters', chunk(1:2) == 'DE' .and. amount == 2)
    close(unit)
  end subroutine eor_read_status
  subroutine ok_nonadvance_status(stat)
    integer, intent(out) :: stat
    integer :: unit
    integer :: amount
    character(len=3) :: chunk
    open(newunit=unit, status='scratch', action='readwrite')
    write(unit,'(a)') 'ABCDE'
    rewind(unit)
    chunk = '###'
    if (chunk /= '###') error stop
    read(unit,'(a)',advance='no',iostat=stat,size=amount) chunk
    call require_true('nonadvancing zero-status read defines sentinel target', chunk == 'ABC' .and. amount == 3)
    close(unit)
  end subroutine ok_nonadvance_status
end program i169o_is_iostat_eor_actual
