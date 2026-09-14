program assumed_descriptor
    use iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_char, &
        c_signed_char, c_short, c_long, c_long_long, c_size_t, &
        c_int8_t, c_int16_t, c_int32_t, c_int64_t, &
        c_int_least8_t, c_int_least16_t, c_int_least32_t, c_int_least64_t, &
        c_int_fast8_t, c_int_fast16_t, c_int_fast32_t, c_int_fast64_t, &
        c_intmax_t, c_intptr_t, c_ptrdiff_t
    implicit none
    integer, parameter :: integer_kinds(*) = [ &
        c_signed_char, c_short, c_int, c_long, c_long_long, c_size_t, &
        c_int8_t, c_int16_t, c_int32_t, c_int64_t, &
        c_int_least8_t, c_int_least16_t, c_int_least32_t, c_int_least64_t, &
        c_int_fast8_t, c_int_fast16_t, c_int_fast32_t, c_int_fast64_t, &
        c_intmax_t, c_intptr_t, c_ptrdiff_t]
    integer, parameter :: real_kinds(*) = [c_float, c_double, c_long_double]
    integer(c_int) :: whole = 17_c_int
    real(kind(0.0)) :: single_value = 0.0
    real(kind(0.0d0)) :: double_value = 0.0d0
    character(len=3) :: short_text = 'oak'
    character(len=5) :: long_text = 'birch'
    integer(c_int) :: aliases(21) = 0_c_int
    interface
        integer(c_int) function check_descriptor(x, tag, aliases) bind(c, name='check_descriptor')
            import c_int
            type(*), intent(in) :: x(..)
            integer(c_int), value :: tag
            integer(c_int), intent(in) :: aliases(*)
        end function
    end interface
    print *, 'ISO_C_BINDING kinds (int,float,double,char):', c_int, c_float, c_double, c_char
    print *, 'actual kinds (int,real,double,char):', kind(whole), kind(single_value), &
        kind(double_value), kind(short_text)
    aliases = merge(1_c_int, 0_c_int, integer_kinds == c_int .and. integer_kinds >= 0)
    call forward(whole, 1_c_int, aliases)
    aliases = 0_c_int
    aliases(1:3) = merge(1_c_int, 0_c_int, real_kinds == kind(single_value) .and. real_kinds >= 0)
    call forward(single_value, 2_c_int, aliases)
    aliases = 0_c_int
    aliases(1:3) = merge(1_c_int, 0_c_int, real_kinds == kind(double_value) .and. real_kinds >= 0)
    call forward(double_value, 3_c_int, aliases)
    aliases = 0_c_int
    aliases(1) = merge(1_c_int, 0_c_int, c_char == kind(short_text) .and. c_char >= 0)
    call forward(short_text, 4_c_int, aliases)
    call forward(long_text, 5_c_int, aliases)
contains
    subroutine forward(x, tag, aliases)
        type(*), intent(in) :: x(..)
        integer(c_int), intent(in) :: tag
        integer(c_int), intent(in) :: aliases(21)
        integer(c_int) :: status
        if (all(aliases == 0_c_int)) then
            print *, 'no supported C type/kind mapping for descriptor tag:', tag
            error stop 'descriptor-profile-unavailable'
        end if
        status = -1_c_int
        status = check_descriptor(x, tag, aliases)
        if (status /= 0_c_int) then
            print *, 'descriptor tag/status:', tag, status
            error stop 'assumed-type-descriptor'
        end if
    end subroutine
end program
