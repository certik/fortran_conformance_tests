program legacy_real_kinds
    use iso_fortran_env, only: real_kinds, real32, real64, real128
    implicit none
    integer, parameter :: dk = kind(0.0d0)
    integer, parameter :: selected_qp = merge(real128, real64, real128 > 0)
    ! Safe selectors permit an absent optional method to reach STOP 77.
    integer, parameter :: sk = merge(real32, dk, real32 >= 0)
    integer, parameter :: dp = merge(real64, dk, real64 >= 0)
    integer, parameter :: qk = merge(selected_qp, dk, selected_qp >= 0)
    real(sk) :: zs = 0.0_sk
    real(dp) :: zd = 0.0_dp
    real(qk) :: zq = 0.0_qk
    if (size(real_kinds) < 2) error stop 1
    if (.not. any(real_kinds == kind(0.0))) error stop 2
    if (.not. any(real_kinds == dk)) error stop 3
    if (precision(0.0d0) <= precision(0.0)) error stop 4
    if (precision(0.0d0) < 10 .or. range(0.0d0) < 37) error stop 5
    if (real32 /= 4 .or. real64 /= 8) stop 77
    if (dk /= real64) stop 77
    if (selected_qp < 0) stop 77
    if (.not. any(real_kinds == real32)) error stop 6
    if (.not. any(real_kinds == real64)) error stop 7
    if (.not. any(real_kinds == selected_qp)) error stop 8
    if (radix(zs) /= 2 .or. radix(zd) /= 2 .or. radix(zq) /= 2) stop 77
    if (digits(zs) < 3 .or. digits(zd) < 3 .or. digits(zq) < 3) stop 77
    if (range(zs) < 1 .or. range(zd) < 1 .or. range(zq) < 1) stop 77
    print *, 'default,double,real32,real64,real128,selected_qp'
    print *, kind(0.0), dk, real32, real64, real128, selected_qp
    if (real128 == 0) print *, 'REAL128 zero uses the retained REAL64 fallback'
end program
